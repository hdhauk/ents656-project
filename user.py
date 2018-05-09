import errors as err
import rf
import numpy as np
import tower as Tower
import sys


def errprint(*args, **kwargs):
    """ prints error messages to stderr
    """
    print(*args, file=sys.stderr, **kwargs)


def init_users(n, user_cfg):
    """Initialize n default users with IDs 0-n."""
    users = []
    for id in range(n):
        users.append(User(id, user_cfg))
    return users


class User:
    def __init__(self, id, user_cfg, pos=-1):
        self.id = id

        # config independent
        self.pos = pos  # float
        self.direction = 0  # +1 = moving toward base station, -1 = moving toward small cell
        self.connected_to = None
        self.wants_to_call = False
        self.time_remaining = 0

        # config dependent
        self.height = user_cfg.height
        self.rsl_threshold = user_cfg.rsl_threshold
        self.avg_call_duration = user_cfg.avg_call_duration * 60  # convert from min to sec
        self.mall_speed = user_cfg.mall_speed
        self.parking_speed = user_cfg.parking_speed
        self.road_speed = user_cfg.road_speed

    def is_outside(self, geometry):
        if self.pos == -1:
            raise err.InitializationError

        return self.pos > geometry.parking_start

    def on_road(self, geometry):
        """Return true if user is on the road."""
        if self.pos == -1:
            raise err.InitializationError
        return self.pos > geometry.parking_end

    def update_pos(self, geometry):
        """Update postion of user based on direction of travel and position."""
        speed = self.road_speed if self.on_road(geometry) else self.mall_speed

        self.pos += speed * self.direction

    def attempt_call(self, geometry, primary, secondary):
        """Attempt to establish connection to towers."""

        rsl = rf.RSL(geometry, self, primary)

        try:
            # attempt primary
            try:
                # connect may throw connection error
                primary.connect(self, rsl)

                # connected successfully, save tower type for finishing up
                tower_type = primary.tower_type

            except err.ConnectionError as e:
                # try secondary, similar logic as primary

                # check signal to secondary
                rsl = rf.RSL(geometry, self, secondary)

                secondary.connect(self, rsl, primary=False)
                tower_type = secondary.tower_type

                primary.saved_by_secondary()

        except err.ConnectionError as e:
            # failed to connect to any. this will impact the GOS
            primary.failed_to_connect()
            return

        # succeeded in connection to a tower
        self.time_remaining = rf.call_time(self.avg_call_duration)
        self.connected_to = tower_type

    def random_pos(self, geometry):
        """Return a random position in the workspace, and the direction
        of travel based on where the position is."""
        sector = np.random.random_sample()

        # compute intervals
        road_length = geometry.road_end - geometry.road_start
        parking_length = geometry.road_start - geometry.parking_start
        mall_length = geometry.mall_end

        on_road = 0.0 < sector < 0.2
        in_parking = 0.2 <= sector < 0.5

        if on_road:
            dir = -1
            pos = geometry.road_start + road_length * np.random.random_sample()
        elif in_parking:
            dir = -1
            pos = geometry.parking_start + parking_length * np.random.random_sample()
        else:
            # mall
            dir = 1
            pos = mall_length * np.random.random_sample()

        return pos, dir

    def update_calltime(self):
        """Decrements the calltime with 1 second."""
        self.time_remaining -= 1
        return self.time_remaining < 0

    def disconnect(self):
        """Closes connection on user."""
        self.pos = -1.0
        self.connected_to = None
        self.wants_to_call = False
        self.time_remaining = 0

    def drop(self):
        """Reset user to a non-connected state.
        Left in order to have a 1-1 relation with methods
        on tower.
        """
        self.disconnect()

    def on_timestep(self, geometry, base_station, small_cell):
        if self.connected_to is None:
            # user doesn't have a connection

            # check if the user want's to call
            self.wants_to_call = rf.want_call()
            if self.wants_to_call:
                # spawn user at som position
                self.pos, self.direction = self.random_pos(geometry)

                # try to connect to the correct tower
                if self.is_outside(geometry):
                    self.attempt_call(geometry, base_station, small_cell)
                else:
                    self.attempt_call(geometry, small_cell, base_station)
        else:
            # user already have a connection
            self.update_pos(geometry)

            # determine what station the user are connected to
            if self.connected_to == Tower.BASE_STATION:
                primary = base_station
                secondary = small_cell
            else:
                primary = small_cell
                secondary = base_station

            done = self.update_calltime()
            if done:
                # close connection gracefully
                primary.disconnect(self, call_done=True)
                self.disconnect()
                return

            # check if user is leaving the area on either side
            end = base_station.pos if self.direction == 1 else small_cell.pos
            if rf.near(1, self.pos, end):
                # count as successful handover
                primary.handover_attempt()
                primary.hand_over(self)
                self.disconnect()
                return

            # check if user will drop the call due to poor RSL
            rsl_pri = rf.RSL(geometry, self, primary)
            if rsl_pri < self.rsl_threshold:
                # print("lost signal at pos=%.1f --> rsl = %.2f" % (self.pos, rsl_pri))
                # print("lost sig at pos=%.1f, connected to = %s" %(self.pos, "base station" if
                # primary.tower_type == Tower.BASE_STATION else "small cell"))
                primary.drop(self)
                self.drop()
                return

            # check if user can/should hand over to other tower
            rsl_alt = rf.RSL(geometry, self, secondary)
            potential_handoff = rsl_alt > rsl_pri
            if potential_handoff:
                # record attempted handoff
                primary.handover_attempt()

                try:
                    secondary.connect(self, rsl_alt)  # can raise ConnectionError
                    self.connected_to = secondary.tower_type
                    primary.hand_over(self)

                except err.ConnectionError as e:
                    # no free channels on secondary

                    # register handover failure on primary
                    primary.handover_failure(self)
