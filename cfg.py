import json
import tower as twr


def read_json(path):
    """read config file in json format from path"""
    with open(path) as json_data:
        d = json.load(json_data)
        return d


class Geometry():
    """Store all distances of the simulation.
    All are distance from origin in meter. Also contain wall penetration
    loss as this have a logical connection to the wall and where it is.
    """

    def __init__(self, config_dict):
        """Extract geomtry from config dictionary."""
        self.mall_start = 0.0
        self.mall_end = float(config_dict["distances_m"]["parking_start"])

        self.hall_start = float(config_dict["distances_m"]["mall_entry_start"])
        self.hall_end = self.mall_end

        self.parking_start = float(config_dict["distances_m"]["parking_start"])
        self.parking_end = float(config_dict["distances_m"]["parking_end"])

        self.road_start = self.parking_end
        self.road_end = float(config_dict["distances_m"]["base_station"])

        self.wall_loss = float(config_dict["path_loss"]["wall_penetration_dB"])


class SimOptions():
    """Store all simulation options."""

    def __init__(self, config_dict, seed=0):
        self.num_users = int(config_dict["user"]["num_users"])
        self.call_rate = float(config_dict["user"]["call_rate_lambda"])
        self.avg_call_duration = float(config_dict["user"]["avg_call_duration_m"])
        self.seed = seed

        self.timestep = int(config_dict["simulation"]["timestep_sec"])
        self.duration = int(config_dict["simulation"]["duration_hour"])
        self.iterations = 3600 * self.duration

        # probabilities for user spawn (calling) locations
        self.prob_spawn_mall = float(config_dict["user"]["probabilities"]["in_mall"])
        self.prob_spawn_parking = float(config_dict["user"]["probabilities"]["in_parking_lot"])
        self.prob_spawn_road = 1 - self.prob_spawn_mall - self.prob_spawn_parking

        # shadowing parameters
        self.shadow_mean = config_dict["path_loss"]["shadowing"]["mean_dB"]
        self.shadow_sigma = config_dict["path_loss"]["shadowing"]["sigma_dB"]
        self.shadow_segment_length = int(config_dict["path_loss"]["shadowing"]["segment_length_m"])

    def set_duration(self, duration):
        self.iterations = duration * 3600
        self.duration = duration


class UserOptions:
    """Store user specific options."""

    def __init__(self, config_dict):
        self.mall_speed = float(config_dict["user"]["speed_m/s"]["mall"])
        self.parking_speed = self.mall_speed
        self.road_speed = float(config_dict["user"]["speed_m/s"]["road"])

        self.rsl_threshold = config_dict["user"]["rx_threshold_dBm"]
        self.height = float(config_dict["user"]["height_m"])
        self.avg_call_duration = int(config_dict["user"]["avg_call_duration_m"])


class TowerOptions:
    """Store tower specific options."""

    def __init__(self, config_dict, twr_type):
        key = ""
        if twr_type == twr.BASE_STATION:
            key = "base_station"
            self.pos = float(config_dict["distances_m"][key])
        elif twr_type == twr.SMALL_CELL:
            key = "small_cell"
            self.pos = 0.0

        self.height = float(config_dict[key]["height_m"])
        self.EIRP = float(config_dict[key]["EIRP_dBm"])
        self.channels = float(config_dict[key]["traffic_channels"])
        self.freq = float(config_dict[key]["frequency_MHz"])
        self.twr_type = twr_type


def valid_distance(dist_m):
    """check that distance is:
    * non-negative 
    * an integer
    * devisable by 100
    * above 3000
    """
    if type(dist_m) != int:
        return False

    if 0 < dist_m < 3000:
        return False

    if dist_m % 100 != 0:
        return False

    return True
