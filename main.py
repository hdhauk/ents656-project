#!/usr/bin/env python
import argparse
import sys
import numpy as np
import time

import cfg
import output
import rf
import simulation as sim
import tower as twr
import user as usr


def errprint(*args, **kwargs):
    """ prints error messages to stderr """
    print(*args, file=sys.stderr, **kwargs)


# parse command line arguments. cmd args override options in config file
parser = argparse.ArgumentParser(description='GSM Simulation.')
parser.add_argument("-c", "--config", type=str, default="config.json")
parser.add_argument("-t", "--sim_time", type=int, nargs=1, default=-1,
                    help="simulation time in hours")
parser.add_argument("-d", "--distance", type=int, nargs=1, default=-1,
                    help="distance between towers in meters")
parser.add_argument("-s", "--silent", action='store_true',
                    help="don't show status updates every hour")
parser.add_argument("-ss", "--supersilent", action='store_true', help="don't even shown summary")
parser.add_argument("-p", "--plot", action='store_true',
                    help="plot handover histogram when simulation is done")
parser.add_argument("-m", "--multithread", action='store_true',
                    help="run 5 simulations concurrently")
parser.add_argument("-o", "--output", type=str, default="results/sim",
                    help="name of output files (for multi thread)")
parser.add_argument("--seed", type=int, nargs=1, default=-1, help="seed rng")
args = parser.parse_args()

config = cfg.read_json(args.config)

# extract options from config dictionary
sim_opts = cfg.SimOptions(config)
user_opts = cfg.UserOptions(config)
geometry = cfg.Geometry(config)
base_opts = cfg.TowerOptions(config, twr.BASE_STATION)
small_opts = cfg.TowerOptions(config, twr.SMALL_CELL)

# override config file if flags are set
if args.sim_time != -1:
    if not (0 < args.sim_time[0] < 1000):
        errprint("please use a non-insane simulation time")
        sys.exit(1)
    sim_opts.set_duration(args.sim_time[0])
if args.distance != -1:
    if not cfg.valid_distance(args.distance[0]):
        errprint("please use a valid distance")
        sys.exit(1)
    geometry.road_end = args.distance[0]

# seed rng
seed = int(time.time()) if args.seed == -1 else args.seed[0]
sim_opts.seed = seed
np.random.seed(seed)

# set up simulation
base_station = twr.Tower(base_opts)
small_cell = twr.Tower(small_opts)
users = usr.init_users(sim_opts.num_users, user_opts)

# pre compute random values (for performance)
rf.init_shadowing(sim_opts, geometry)
max_possible_dails = sim_opts.num_users * sim_opts.iterations
rf.init_call_probabilities(max_possible_dails, sim_opts.call_rate)

if args.multithread:
    # run simulation concurrently
    print("multi threading activated")
    sim.multi_sim(base_opts, small_opts, user_opts, sim_opts, geometry, args, 5)
    exit(0)
else:
    # run sim once
    stats = sim.simulate(base_station, small_cell, users, geometry, sim_opts, args)

# print summaries
if not args.supersilent:
    output.print_sim_summary(geometry, sim_opts, stats["runtime"])
    output.print_tower_summary(base_station, "Summary Base Station")
    output.print_tower_summary(small_cell, "Summary Small Cell")

# plotting
if args.plot:
    output.handover_histogram(base_station.dump_handoff_data())
