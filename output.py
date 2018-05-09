import matplotlib.pyplot as plt
import tower


# PLOTTING STUFF

def handover_histogram(handover_data):
    plt.title("Handovers")
    plt.subplot(211)
    plt.hist(handover_data[0], bins=600, range=(1, 2999))
    plt.hist(handover_data[1], bins=600, range=(1, 2999))
    plt.legend(("Successful handovers", "Unsuccessful handovers"))
    plt.xlabel("distance [m]")

    plt.subplot(212)
    plt.hist(handover_data[0], bins=80, range=(180, 220))
    plt.hist(handover_data[1], bins=80, range=(180, 220))
    plt.xlim(180, 220)
    plt.legend(("Successful handovers", "Unsuccessful handovers"))
    plt.axvline(x=200, color='b', linestyle='-')
    plt.axvline(x=190, color='b', linestyle='-')
    plt.xlabel("distance [m]")

    plt.show()


# PRINTING STUFF

# helper functions
def __header(description):
    print(" {} ".format(description).center(52, "="))


def __footer():
    print("-" * 52 + "\n")


def __tower_options(t):
    print("parameters:")
    print("\theight:                         %4.1f [m]" % t.height)
    print("\tEIRP:                           %4.1f [dBm]" % t.EIRP)
    print("\ttraffic channels:               %4d" % t.channels)
    print("\tposition:                       %4d [m]" % t.pos)
    print("\tfrequency:                      %4d [MHz]" % t.freq)
    print("\tsmall_cell:                    %5r" % (t.tower_type == tower.SMALL_CELL))


def __tower_status(t):
    print("a. # channels in use:                  %5d" % t._channels_in_use)
    print("b. # call attempts:                    %5d" % t._connections_attempts)
    print("c. # successful initial connection:    %5d" % t._conns_established)
    print("d. # successfully completed:           %5d" % (t._user_hung_up + t._handover_success))
    print("      # closed by user (call done):    %5d" % t._user_hung_up)
    print("      # handed over to other tower:    %5d" % t._handover_success)
    print("e. handovers")
    print("      # attempts:                      %5d" % t._handover_attempt)
    print("      # successes:                     %5d" % t._handover_success)
    print("      # failures:                      %5d" % t._handover_failure)
    print("f. # call drops:                       %5d" % t._dropped)
    print("g. blocks")
    print("      # due to capacity:               %5d" % t._blocked_no_chan)
    print("      # due to signal:                 %5d" % t._blocked_no_sig)
    print("h. misc")
    print("      # times saved by secondary:      %5d" % t._saved_by_secondary)


# public functions
def print_tower_status(tower, description="STATUS"):
    __header(description)
    __tower_status(tower)
    __footer()


def print_tower_summary(tower, description="SUMMARY"):
    __header(description)
    __tower_options(tower)
    __tower_status(tower)
    __footer()


def print_sim_summary(geometry, sim_opts, sim_duration):
    print(" {} ".format("Simulation Summary").center(50, "="))
    print("simulation:")
    print("\tcomputation time:       %4.1f [sec]" % sim_duration)
    print("\tduration:               %4d [hour]" % sim_opts.duration)
    print("\ttime step:              %4d [sec]" % sim_opts.timestep)
    print("\trng seed:         %10d" % sim_opts.seed)

    print("geometry:")
    length_mall = geometry.mall_end
    length_parking = geometry.parking_end - geometry.parking_start
    length_road = geometry.road_end - geometry.parking_end

    print("\tlength mall:            %4d [m]" % length_mall)
    print("\tlength parking:         %4d [m]" % length_parking)
    print("\tlength road:            %4d [m]" % length_road)

    print("-" * 50 + "\n")


def print_aggregate_stats(stats_list):
    aggregate = {
        "total_call_attempts": 0,
        "total_call_failures": 0,
        "total_fail_no_signal": 0,
        "total_fail_no_channel": 0,
        "total_handover_attempts": 0,
        "total_handover_success": 0,
        "total_handover_failures": 0,
        "total_dropped": 0,
        "total_failed_to_connect": 0,
        "total_saved_by_secondary": 0,
        "avg_calls_base": 0,
        "avg_calls_cell": 0,

    }
    for stats in stats_list:
        aggregate["total_call_attempts"] += stats["total_call_attempts"]
        aggregate["total_call_failures"] += stats["total_call_failures"]
        aggregate["total_fail_no_signal"] += stats["total_fail_no_signal"]
        aggregate["total_fail_no_channel"] += stats["total_fail_no_channel"]
        aggregate["total_handover_attempts"] += stats["total_handover_attempts"]
        aggregate["total_handover_failures"] += stats["total_handover_failures"]
        aggregate["total_handover_success"] += stats["total_handover_success"]
        aggregate["total_dropped"] += stats["total_dropped"]
        aggregate["total_failed_to_connect"] += stats["total_failed_to_connect"]
        aggregate["total_saved_by_secondary"] += stats["total_saved_by_secondary"]
        aggregate["avg_calls_base"] += stats["avg_calls_base"]
        aggregate["avg_calls_cell"] += stats["avg_calls_cell"]

    aggregate["avg_calls_base"] /= len(stats_list)
    aggregate["avg_calls_cell"] /= len(stats_list)

    __header("Aggregate statistics")
    print("total for all simulations")
    print("  call attempts:                              %6d" % aggregate["total_call_attempts"])
    print("  call failures:                              %6d" % aggregate["total_call_failures"])
    print("    due to no signal:                         %6d" % aggregate["total_fail_no_signal"])
    print("    due to no channels:                       %6d" % aggregate["total_fail_no_channel"])
    print("  calls dropped (lost signal):                %6d" % aggregate["total_dropped"])
    print("  failed to connect:                          %6d" % aggregate["total_failed_to_connect"])
    print("  primary \"saved\" by secondary:               %6d" % aggregate["total_saved_by_secondary"])
    print("  handover attempts:                          %6d" % aggregate["total_handover_attempts"])
    print("  handover successes:                         %6d" % aggregate["total_handover_success"])
    print("  handover failures:                          %6d" % aggregate["total_handover_failures"])
    print("  avg channels in use (base station):         %6d" % aggregate["avg_calls_base"])
    print("  avg channels in use (small cell):           %6d" % aggregate["avg_calls_cell"])

    __header("Q & A")
    print("Q: How many dropped calls occur?")
    print("A: %d (out of %d attempts)" %
          (aggregate["total_call_failures"], aggregate["total_call_attempts"]))
    print("   {} attempts ignoring handover attempts"
          .format(aggregate["total_call_attempts"] - aggregate["total_handover_attempts"]))
    print()

    print("Q: What percentage of call attempts end up as ")
    print("   dropped calls (GOS)?")
    try:
        gos = 100 * float(aggregate["total_failed_to_connect"] - aggregate["total_saved_by_secondary"]) / \
              float(aggregate["total_call_attempts"])
    except ZeroDivisionError:
        gos = -1
    print("A: %.3f%%" % gos)
    print()

    print("Q: How many calls blocked due to capacity vs.")
    print("   due to signal strength?")
    print("A:")
    blocked = float(aggregate["total_fail_no_channel"] + aggregate["total_fail_no_signal"])
    try:
        percent_no_chan = 100 * float(aggregate["total_fail_no_channel"]) / float(blocked)
        percent_no_sig = 100 - percent_no_chan
    except ZeroDivisionError:
        percent_no_chan = -1
        percent_no_sig = -1

    print("   due to capacity:         %4d [%5.1f%%]" % (aggregate["total_fail_no_channel"], percent_no_chan))
    print("   due to signal:           %4d [%5.1f%%]" % (aggregate["total_fail_no_signal"], percent_no_sig))
