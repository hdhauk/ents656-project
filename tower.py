import errors as err

# constants used for tower_type
BASE_STATION = 1
SMALL_CELL = 2


class Tower:

    def defaults(self):
        self.height = 10.0
        self.EIRP = 30.0
        self.channels = 30
        self.freq = 1000
        self.users = {}
        self.pos = 0
        self.tower_type = SMALL_CELL

    def __init__(self, options=None, debug=False):
        if options is None:
            self.defaults()
        else:
            self.height = options.height
            self.EIRP = options.EIRP
            self.channels = options.channels
            self.freq = options.freq
            self.pos = options.pos
            self.tower_type = options.twr_type

        self._debug = debug

        # statistics data
        self.reset_counters()

    def reset_counters(self):
        self.users = {}
        self._dropped = 0
        self._blocked_no_sig = 0
        self._blocked_no_chan = 0
        self._channels_in_use = 0
        self._handover_success = 0
        self._handover_failure = 0
        self._handover_failure_locations = []
        self._handover_success_locations = []
        self._handover_attempt = 0
        self._successful_conns = 0
        self._conns_established = 0
        self._connections_attempts = 0
        self._failed_to_connect = 0
        self._user_hung_up = 0
        self._saved_by_secondary = 0

    def connect(self, user, rsl, primary=True):
        """Associates the user to the tower if available capacity, and acceptable rsl.
        If the connection is made with primary=False (aka. the user is trying to
        connect to this tower only because it failed to connect to its primary
        tower), the only statistics logging will be made if the connection is successful.
        """
        # don' count attempt yet if secondary.
        # If we fail we want to disregard this attempt altogether
        if primary:
            self._connections_attempts += 1

        signal_too_weak = rsl < user.rsl_threshold
        if signal_too_weak:
            if primary:
                self._blocked_no_sig += 1
            raise err.ConnectionError(err.LOW_SIGNAL)

        if self._channels_in_use >= self.channels:
            if primary:
                self._blocked_no_chan += 1
            raise err.ConnectionError(err.NO_FREE_CHANNELS)

        # now that we know the connection succeeded we must register the attempt if were a secondary
        if not primary:
            self._connections_attempts += 1

        self._add(user)
        self._conns_established += 1

    def _add(self, user):
        """Adds user to the tower. Assuming it can."""
        self._channels_in_use += 1
        if self._debug:
            print("user #%d added. channels available: %d/%d" %
                  (user.id, self._channels_in_use, self.channels))

    def _remove(self, user):
        """Removes user from the tower. Assuming it can."""
        if self._channels_in_use <= 0 and not self._debug:
            raise ValueError("cannot have negative channels in use")

        self.users[user.id] = False
        self._channels_in_use -= 1

        if self._debug:
            print("user #%d removed. channels available: %d/%d" %
                  (user.id, self._channels_in_use, self.channels))

    def disconnect(self, user, call_done=False):
        self._remove(user)
        self._successful_conns += 1
        if call_done:
            self._user_hung_up += 1

    def drop(self, user):
        """Dropped call due to user lost signal."""
        self._remove(user)
        self._dropped += 1

    def failed_to_connect(self):
        """Dropped call. User were never able to connect"""
        self._failed_to_connect += 1

    def hand_over(self, user):
        self._remove(user)
        self._handover_success += 1
        self._handover_success_locations.append(user.pos)

    def handover_failure(self, user):
        self._handover_failure += 1
        self._handover_failure_locations.append(user.pos)

    def handover_attempt(self):
        self._handover_attempt += 1

    def saved_by_secondary(self):
        self._saved_by_secondary += 1

    def dump_handoff_data(self):
        return (self._handover_success_locations, self._handover_failure_locations)
