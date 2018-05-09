import multiprocessing as multiproc
import os
import sys
import time
import numpy as np

import output
import rf
import tower as twr
import user as usr


def simulate(base_station, small_cell, users, geometry, sim_opts, cli_args):
    start_time = time.time()

    # run simulation
    tot_bstn, tot_cell = 0, 0
    for i in range(sim_opts.iterations):

        # print status updates
        status_update = (not cli_args.silent and (i % 3600 == 0 and i != 0))
        if status_update and not cli_args.supersilent:
            base_description = "Base Station: t = {} hrs".format(i // 3600)
            small_description = "Small Cell:  t = {} hrs".format(i // 3600)

            output.print_tower_status(base_station, description=base_description)
            output.print_tower_status(small_cell, description=small_description)

        tot_bstn += base_station._channels_in_use
        tot_cell += small_cell._channels_in_use
        # simulate timestep
        for u in users:
            u.on_timestep(geometry, base_station, small_cell)

    end_time = time.time()
    runtime = end_time - start_time

    output.print_sim_summary(geometry, sim_opts, runtime)
    output.print_tower_summary(base_station, "Summary Base Station")
    output.print_tower_summary(small_cell, "Summary Small Cell")

    avg_calls_base = float(tot_bstn) / float(i)
    avg_calls_cell = float(tot_cell) / float(i)

    # summarize simulation
    total_call_attempts = 0
    total_call_failures = 0
    total_fail_no_signal = 0
    total_fail_no_channel = 0
    total_handover_success = 0
    total_handover_failures = 0
    total_handover_attempts = 0
    total_dropped = 0
    total_failed_to_connect = 0
    total_saved_by_secondary = 0
    for n in [base_station, small_cell]:
        # don't count ongoing calls as these might go both ways
        total_call_attempts += n._connections_attempts
        total_call_failures += n._blocked_no_sig + n._blocked_no_chan
        total_fail_no_signal += n._blocked_no_sig
        total_fail_no_channel += n._blocked_no_chan
        total_handover_success += n._handover_success
        total_handover_failures += n._handover_failure
        total_handover_attempts += n._handover_attempt
        total_dropped += n._dropped
        total_failed_to_connect += n._failed_to_connect
        total_saved_by_secondary += n._saved_by_secondary

    stats = {
        "runtime": runtime,
        "total_call_attempts": total_call_attempts,
        "total_call_failures": total_call_failures,
        "total_fail_no_signal": total_fail_no_signal,
        "total_fail_no_channel": total_fail_no_channel,
        "total_handover_success": total_handover_success,
        "total_handover_failures": total_handover_failures,
        "total_handover_attempts": total_handover_attempts,
        "total_dropped": total_dropped,
        "total_failed_to_connect": total_failed_to_connect,
        "total_saved_by_secondary": total_saved_by_secondary,
        "avg_calls_base": avg_calls_base,
        "avg_calls_cell": avg_calls_cell,

    }
    return stats


def concurrent_sim(base_opts, small_opts, user_opts, sim_opts, geometry,
                   cli_args, queue, seed, name=""):
    """Run one concurrent instance of a simulation. All printing is done to a
    named file instead of stdout to avoid nonsensical cluttering by multiple
    threads."""
    # redirect stdout
    filename = name if name != "" else "pid_{}.txt".format(os.getpid())
    sys.stdout = open(filename, mode="w")

    # precompute random values (for performance)
    # must be done for each process
    np.random.seed(seed)
    rf.init_shadowing(sim_opts, geometry)
    max_possible_dails = sim_opts.num_users * sim_opts.iterations
    rf.init_call_probabilities(max_possible_dails, sim_opts.call_rate)

    # set up simulation
    base_station = twr.Tower(base_opts)
    small_cell = twr.Tower(small_opts)
    users = usr.init_users(sim_opts.num_users, user_opts)

    # simulate normally
    stats = simulate(base_station, small_cell, users, geometry, sim_opts, cli_args)
    # save statistics
    queue.put(stats)


def multi_sim(base_opts, small_opts, user_opts, sim_opts, geometry, cli_args, times=5):
    """Spawn multiple processes running the simulation concurrently."""
    Q = multiproc.Queue()
    start_time = time.time()

    # spawn simulation threads
    processes = []
    for i in range(times):
        name = cli_args.output + "_" + str(i) + ".txt"
        seed = sim_opts.seed + i
        sim_opts.seed = seed
        proc = multiproc.Process(target=concurrent_sim,
                                 args=(base_opts, small_opts, user_opts,
                                       sim_opts, geometry, cli_args, Q, seed, name))
        processes.append(proc)
        proc.start()

    # wait for simulations to complete
    for proc in processes:
        proc.join()

    end_time = time.time()
    runtime = end_time - start_time
    print("all %d simulations done in %d seconds" % (times, runtime))

    # get results from queue
    stats = []
    for i in range(times):
        stats.append(Q.get())

    output.print_aggregate_stats(stats)
