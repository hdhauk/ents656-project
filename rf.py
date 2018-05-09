import numpy as np
from math import log10

import tower as Tower
import errors as err

# shadowing data
_shadows = []


def init_shadowing(sim_opts, geometry):
    """Initalize shadowing values for all postitions between small cell
    and base station. No shadowing inside the mall."""

    global _shadows
    unique_samples = int((geometry.road_end - geometry.mall_end) // sim_opts.shadow_segment_length)

    samples = np.random.normal(
        sim_opts.shadow_mean, sim_opts.shadow_sigma, unique_samples)

    # upscale samples to 1m resolution and append with zero values for inside mall
    road = np.repeat(samples, sim_opts.shadow_segment_length)
    mall = np.zeros((1, int(geometry.mall_end)))
    _shadows = np.append(mall, road)


def get_shadowing(pos):
    """Return precomputed shadowing values for position."""
    try:
        pos_int = int(pos)
        return _shadows[pos_int]
    except IndexError:
        raise err.InitializationError


# call probability data
_rand_bool = None
_rand_bool_init = False
_rand_bool_idx = 0
_rand_bool_num = 0
_rand_bool_prob = 0


def init_call_probabilities(size, calls_per_hrs):
    """Precomputes table of boolean call probabilities shared for all users."""
    global _rand_bool, _rand_bool_init, _rand_bool_num, _rand_bool_prob

    _rand_bool_prob = float(calls_per_hrs) / 3600.0
    _rand_bool = np.random.rand(size) < _rand_bool_prob
    _rand_bool_init = True
    _rand_bool_num = size


def want_call():
    """Returns precomputed call probabilities. Wraps around after size calls."""
    global _rand_bool
    global _rand_bool_idx
    global _rand_bool_num
    global _rand_bool_init
    global _rand_bool_prob

    if not _rand_bool_init:
        raise err.InitializationError("run \"init_call_probabilities\" first")
    _rand_bool_idx += 1

    # in case we initialize too few first time
    if _rand_bool_idx % _rand_bool_num == 0:
        # double size for amortization effect
        _rand_bool_num *= 2
        _rand_bool = np.random.rand(_rand_bool_num) < _rand_bool_prob
    return _rand_bool[_rand_bool_idx % _rand_bool_num]


def call_time(mean):
    """Return an exponentially distributed call duration."""
    return int(np.random.exponential(mean))


def rayleigh(mean, sigma, samples):
    """Manually compute Rayleigh distributed values.
    Deprecated due to significantly worse performance than
    numpy.random.rayleigh:
    For million function calls:
        rf.rayleigh:               18.72 s
        numpy.random.rayleigh:      5.38 s
    """
    a = np.random.normal(mean, sigma, samples)
    b = np.random.normal(mean, sigma, samples)

    z = a + b * (1j)
    return np.abs(z)


def mag2dB(mag):
    """ Convert magnitude to decibels."""
    return 10 * log10(mag)


def near(threshold, dist1, dist2):
    """Return true if distances is closes than
    threshold from each other.
    """
    return abs(float(dist1) - float(dist2)) <= float(threshold)


def get_fading_complex():
    """Compute fading by sampeling a Rayleigh distribution 10 times
    and then returning the 2nd lowest value.
    """
    samples = rayleigh(0, 1, 10)

    # extract second smallest element
    second_smallest = get_kth_smallest(samples, 2)
    return mag2dB(second_smallest)


def get_fading():
    """Compute fading by sampeling a Rayleigh distribution 10 times
    and then returning the 2nd lowest value.
    """
    samples = np.random.rayleigh(1, 10)

    # extract second smallest element
    second_smallest = get_kth_smallest(samples, 2)
    return mag2dB(second_smallest)


def get_kth_smallest(array, k):
    """Return the k-th smallest element in array.
    e.g: get 2nd smallest: get_kth_smalles(array, 2).
    Using argpartition we avoid sorting the whole array, only
    partition at the k-th element (like you would do in quicksort).
    """
    if type(k) != int:
        raise TypeError

    indexes = np.argpartition(array, k)
    return array[indexes[:k]][-1]


def _interpolate(dist_in_interval, min_val, max_val, interval_length):
    """Linear interpolation between min_val and max_val.
    Interval assumed to be (0,interval_length)
    """
    if dist_in_interval > interval_length:
        raise ValueError
    if min_val > max_val:
        raise ValueError

    diff = max_val - min_val
    weight = dist_in_interval / interval_length

    return min_val + diff * weight


def get_penetration(geometry, bstn, user):
    """Get and possibly interpolate wall loss."""
    inside = user.pos <= geometry.hall_start
    outside = user.pos >= geometry.mall_end
    small_cell = bstn.tower_type == Tower.SMALL_CELL

    if inside:
        if small_cell:
            return 0
        else:
            return geometry.wall_loss

    elif outside:
        if small_cell:
            return geometry.wall_loss
        else:
            return 0

    else:
        # in hallway
        hall_length = geometry.mall_end - geometry.hall_start
        pos = user.pos - geometry.hall_start
        if small_cell:
            return _interpolate(pos, 0, geometry.wall_loss, hall_length)
        else:
            pos = hall_length - pos
            return _interpolate(pos, 0, geometry.wall_loss, hall_length)


def RSL(geometry, user, tower):
    """Return received signal level from tower experienced by the user."""
    dist_to_tower = abs(user.pos - tower.pos)
    propagation = okamura_hata(dist_to_tower, tower.freq, tower.height, user.height)

    # only compute shadowing if user is connected to the base station
    # if connected to base station and inside mall get_shadowing will
    # return 0.
    shadow = get_shadowing(user.pos) if tower.tower_type == Tower.BASE_STATION else 0.0
    fading = get_fading()
    wall = get_penetration(geometry, tower, user)

    return tower.EIRP - propagation - shadow + fading - wall


def okamura_hata(d_m, f_MHz, h_bstn_m, h_handset_m):
    """Compute propegation loss using Okamura-Hata formula."""
    d_km = d_m / 1000

    # handset height term
    def a(h): return (1.1 * log10(f_MHz) - 0.7) * h - (1.5 * log10(f_MHz) - 0.8)

    return 69.55 + 26.16 * log10(f_MHz) - 13.82 * log10(h_bstn_m) + \
        (44.9 - 6.55 * log10(h_bstn_m)) * log10(d_km) - a(h_handset_m)
