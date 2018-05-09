import unittest
import numpy as np
import sys
import matplotlib.pyplot as plt
import time

import rf
import tower as twr
import user as usr
import cfg


def red(*args, **kwargs):
    """ prints error messages to stderr in red
    """
    print('\033[93m', end="")
    print(*args, file=sys.stderr, **kwargs)
    print('\033[0m', end="")


def fuzzy_equal(a, b, thresh):
    return abs(a - b) < thresh


class TestRF(unittest.TestCase):

    @unittest.skipIf('-plot' in sys.argv, "plot")
    def test_init_shadowing(self):
        length_total = 3000
        length_mall = 200
        length_segment = 10

        config = cfg.read_json("test_files/golden_config.json")
        opts = cfg.SimOptions(config)
        geometry = cfg.Geometry(config)

        rf.init_shadowing(opts, geometry)

        self.assertEqual(len(rf._shadows), length_total,
                         "expected same number of elements as total length")

        # check that first 200 samples are zero
        for i in range(length_mall):
            self.assertEqual(
                rf._shadows[i], 0, "elements inside mall should be zero")

        # check that last 1800 samples are in length 10 non-zero buckets
        for i in range(length_mall, length_total, length_segment):
            val = rf._shadows[i]
            self.assertNotEqual(val, 0, "elements outside should be non-zero")
            for j in range(10):
                self.assertEqual(rf._shadows[i + j], val, "elements in segment should be equal")

        # check variance is 2 dB
        self.assertLess(abs(rf._shadows[200:-1:10].std() - 2), 0.2)

        # check mean is 0
        self.assertLess(abs(rf._shadows[200:-1:10].mean()), 0.3)

    @unittest.skipIf('-plot' in sys.argv, "plot")
    def test_penetration(self):
        # setup
        config = cfg.read_json("test_files/golden_config.json")
        geometry = cfg.Geometry(config)
        user_cfg = cfg.UserOptions(config)
        small_cfg = cfg.TowerOptions(config, twr.SMALL_CELL)
        base_cfg = cfg.TowerOptions(config, twr.BASE_STATION)

        # test from small cell
        small = twr.Tower(small_cfg)
        usr_outside = usr.User(0, user_cfg, pos=201)
        usr_in_entry = usr.User(0, user_cfg, pos=195)
        usr_inside = usr.User(0, user_cfg, pos=189)

        self.assertEqual(rf.get_penetration(geometry, small, usr_outside), 21)
        self.assertEqual(rf.get_penetration(geometry, small, usr_inside), 0)
        self.assertEqual(rf.get_penetration(
            geometry, small, usr_in_entry), 21 / 2)

        # test from base station
        bstn = twr.Tower(base_cfg)
        usr_outside = usr.User(0, user_cfg, pos=201)
        usr_in_entry = usr.User(0, user_cfg, pos=195)
        usr_inside = usr.User(0, user_cfg, pos=189)

        self.assertEqual(rf.get_penetration(geometry, bstn, usr_outside), 0)
        self.assertEqual(rf.get_penetration(geometry, bstn, usr_inside), 21)
        self.assertEqual(rf.get_penetration(
            geometry, bstn, usr_in_entry), 21 / 2)

    @unittest.skipIf('-plot' in sys.argv, "plot")
    def test_interpolation(self):
        val = rf._interpolate(5, 100, 200, 10)
        self.assertEqual(val, 150.0)

        val = rf._interpolate(0, 100, 200, 10)
        self.assertEqual(val, 100)

        val = rf._interpolate(7.5, 100, 200, 10)
        self.assertEqual(val, 175.0)

        val = rf._interpolate(10, 100, 200, 10)
        self.assertEqual(val, 200)

        val = rf._interpolate(5, -200, 200, 10)
        self.assertEqual(val, 0)

        self.assertRaises(ValueError, rf._interpolate, 10.1, 100, 200, 10)
        self.assertRaises(ValueError, rf._interpolate, 5, 201, 200, 10)

    @unittest.skipIf('-plot' in sys.argv, "plot")
    def test_mag2dB(self):
        self.assertEqual(rf.mag2dB(100), 20)
        self.assertEqual(rf.mag2dB(10), 10)

    @unittest.skipIf('-plot' in sys.argv, "plot")
    def test_near(self):
        tests = [
            (5, 190, 200, False),
            (10, 190, 200, True),
            (1, 0, 1, True),
            (1, 3000.0, 2999.0, True)
        ]
        for t in tests:
            got = rf.near(t[0], t[1], t[2])
            self.assertEqual(got, t[3],
                             "near({}, {}, {}) = {}, expected {}"
                             .format(t[0], t[1], t[2], got, t[3]))

    @unittest.skipIf('-plot' in sys.argv, "plot")
    def test_kth_smallest(self):
        tests = [
            (np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]), 2, 2),
            (np.array([-10.0, 40, 22.0, 48, 0]), 1, -10.0),
            (np.array([-10.0, 40, 22.0, 48, 0, 200]), 2, 0.0),
            (np.array([0, 0, 0.0, 0, 0, 0]), 2, 0),

        ]

        for t in tests:
            got = rf.get_kth_smallest(t[0], t[1])
            self.assertEqual(got, t[2],
                             "get_kth_smallest({}, {}) = {}, expected {}"
                             .format(t[0], t[1], got, t[2]))

    @unittest.skipIf('-plot' in sys.argv, "plot")
    def test_call_probabilites(self):
        size = 100000
        calls_per_hour = 1.0
        calls_per_sec = calls_per_hour / 3600.0
        rf.init_call_probabilities(size, calls_per_hour)

        want_num_true = size * calls_per_sec
        got_num_true = 0
        for val in rf._rand_bool:
            if val:
                got_num_true += 1
        self.assertLess(abs(want_num_true - got_num_true), 10)

    @unittest.skipIf('-plot' in sys.argv, "plot")
    def test_user_spawning(self):
        config = cfg.read_json("test_files/golden_config.json")
        user_cfg = cfg.UserOptions(config)
        geometry = cfg.Geometry(config)

        user = usr.User(1, user_cfg)
        positions = []
        n = 100000

        def mall(x): return 0 < x < 200

        def park(x): return 200 < x < 300

        def road(x): return 300 < x < 3000

        for i in range(n):
            pos, _ = user.random_pos(geometry)
            positions.append(pos)

        in_mall = list(filter(mall, positions))
        in_park = list(filter(park, positions))
        on_road = list(filter(road, positions))

        print("n/2 =", n / 2)
        self.assertLess(abs(len(in_mall) - n / 2), 500)
        self.assertLess(abs(len(in_park) - (3 * n / 10)), 500)
        self.assertLess(abs(len(on_road) - n / 5), 500)

    """ plotting """

    @unittest.skipUnless('-plot' in sys.argv, "plot")
    def test_RSL(self):
        config = cfg.read_json("test_files/golden_config.json")

        small_cfg = cfg.TowerOptions(config, twr.SMALL_CELL)
        base_cfg = cfg.TowerOptions(config, twr.BASE_STATION)
        user_cfg = cfg.UserOptions(config)
        geometry = cfg.Geometry(config)
        sim_opts = cfg.SimOptions(config)

        small = twr.Tower(small_cfg)
        bstn = twr.Tower(base_cfg)

        user = usr.User(0, user_cfg)

        np.random.seed(69)
        rf.init_shadowing(sim_opts, geometry)

        # plt.hist(rf._shadows, bins=50, range=(0, 300))
        # plt.show()

        base_signals = []
        small_signals = []
        pos = range(1, 3000, 1)
        for i in pos:
            user.pos = i
            rsl_base = rf.RSL(geometry, user, bstn)
            rsl_small = rf.RSL(geometry, user, small)

            # if rsl_small < user.rsl_threshold and i < 230:
            if False:
                dist_to_tower = abs(user.pos - bstn.pos)
                propagation = rf.okamura_hata(dist_to_tower, bstn.freq, bstn.height, user.height)
                shadow = rf.get_shadowing(user.pos)
                fading = rf.get_fading()
                wall = rf.get_penetration(geometry, bstn, user)
                print("\tpos= %2.1f | propegation: %3.1fdB, shadow:  %4.1fdB, fading:  %3.1fdB, wall:  %3.1fdB " %
                      (i, propagation, shadow, fading, wall))

            base_signals.append(rsl_base)
            small_signals.append(rsl_small)

        plt.title("Recieved Signal Level")

        plt.subplot(211)
        plt.plot(pos, base_signals, color='blue')
        plt.plot(pos, small_signals, color='red')
        plt.legend(("RSL Base Station", "RSL Small Cell"))

        plt.xlabel("distance [m]")
        plt.ylabel("RSL [dBm]")

        plt.axhline(y=user.rsl_threshold, color='orange', linestyle=':')
        plt.axvline(x=200, color='b', linestyle='-')
        plt.axvline(x=190, color='b', linestyle='-')

        plt.subplot(212)
        plt.plot(pos, base_signals, color='blue')
        plt.plot(pos, small_signals, color='red')
        plt.xlim(100, 300)
        plt.ylim(-150, -50)
        plt.legend(("RSL Base Station", "RSL Small Cell"))

        plt.xlabel("distance [m]")
        plt.ylabel("RSL [dBm]")

        plt.axhline(y=user.rsl_threshold, color='orange', linestyle=':')
        plt.axvline(x=200, color='b', linestyle='-')
        plt.axvline(x=190, color='b', linestyle='-')

        plt.show()

    @unittest.skipUnless('-plot' in sys.argv, "plot")
    def test_fading(self):

        n = 100000

        start = time.time()
        values = []
        for i in range(n):
            values.append(rf.get_fading())
        arr = np.array(values)
        runtime1 = time.time() - start

        start = time.time()
        cmplx = []
        for i in range(n):
            cmplx.append(rf.get_fading_complex())
        arr2 = np.array(cmplx)
        runtime2 = time.time() - start

        plt.subplot(211)
        plt.title("#{0} samples with numpy.rayleigh, t = {1:.1f} sec".format(n, runtime1))
        plt.hist(arr, bins=100)
        plt.xlim(-17, 2.5)
        plt.gca().axes.get_xaxis().set_visible(False)

        plt.subplot(212)
        plt.title("#{0} samples with complex method, t = {1:.1f} sec".format(n, runtime2))
        plt.hist(arr, bins=100)
        plt.xlim(-17, 2.5)
        plt.xlabel("decibel")

        plt.show()

    @unittest.skipUnless('-plot' in sys.argv, "plot")
    def test_plot_spawning(self):
        config = cfg.read_json("test_files/golden_config.json")
        user_cfg = cfg.UserOptions(config)
        geometry = cfg.Geometry(config)

        user = usr.User(1, user_cfg)
        positions = []
        n = 100000
        for i in range(n):
            pos, _ = user.random_pos(geometry)
            positions.append(pos)

        def mall(x): return 0 < x < 200

        def park(x): return 200 < x < 300

        def road(x): return 300 < x < 3000

        in_mall = list(filter(mall, positions))
        in_park = list(filter(park, positions))
        on_road = list(filter(road, positions))

        plt.subplot(211)
        plt.hist(positions, bins=[0, 200, 300, 3000], edgecolor='white')
        plt.title("User spawn distribution, {} users".format(n))
        plt.ylim(0, 60000)
        plt.grid()

        plt.subplot(234)
        plt.title("In mall")
        plt.hist(in_mall, bins=50, edgecolor='white')

        plt.subplot(235)
        plt.title("In parking")
        plt.hist(in_park, bins=50, edgecolor='white')

        plt.subplot(236)
        plt.title("On road")
        plt.hist(on_road, bins=50, edgecolor='white')

        plt.show()

    @unittest.skipUnless('-plot' in sys.argv, "plot")
    def test_plot_shadowing(self):
        config = cfg.read_json("test_files/golden_config.json")
        opts = cfg.SimOptions(config)
        geometry = cfg.Geometry(config)

        rf.init_shadowing(opts, geometry)

        plt.title("Shadow values")
        plt.plot(range(len(rf._shadows)), rf._shadows)
        plt.ylabel("dB")
        plt.xlabel("meter")
        plt.show()

    @unittest.skipUnless('-plot' in sys.argv, "plot")
    def test_plot_okamura_hata(self):
        values = []
        for d in range(1, 3000):
            values.append(-rf.okamura_hata(d, 1000.0, 50.0, 1.7))
        plt.plot(values)
        plt.show()


if __name__ == '__main__':
    # don't pass the args to unittest module
    try:
        sys.argv.remove('-plot')
    except ValueError:
        pass

    unittest.main()
