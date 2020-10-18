#! /usr/bin/python3

from subprocess import Popen, call, DEVNULL

import matplotlib.pyplot as plt
import pandas
import os
import argparse

# Make sure we store the db on the correct drive
DB_PATH="./db_bench_data"
BINPATH="./build"

DSTAT_FNAME = "dstat.csv"
LVLDB_FNAME = "foreground_stats.csv"
WORKLOAD = "writerandomburstsbytime"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", default=False)
    parser.add_argument("--plot", action="store_true", default=False)

    args = parser.parse_args()

    if args.run:
        run()

    if args.plot:
        plot()

    if args.plot or args.run:
        print("Done.")
    else:
        print("Warning: No option selected. Doing nothing.")

def run():
    print("# Running Benchmark")
    if os.path.exists(DSTAT_FILENAME):
        os.remove(DSTAT_FILENAME) #dstat appends by default
    dstat = Popen(["dstat", "-gdT", "--output="+DSTAT_FNAME], stdout=DEVNULL)
    print("Dstat initialized.")

    call([BINPATH+"/db_bench", "--benchmarks="+WORKLOAD, "--sleep_duration=10", "--write_time_before_sleep=5", "--workload_duration=40", "--db="+DB_PATH])

    dstat.kill()

def plot():
    print("# Plotting")

    dstat = pandas.read_csv(DSTAT_FNAME, header=3)
    lvldb = pandas.read_csv(LVLDB_FNAME)

    lvldb.time = lvldb.time / (1000*1000)

    start_time = lvldb.time.min()
    end_time = lvldb.time.max()
    elapsed = int(end_time - start_time)

    print("Ran for %i seconds (%i to %i)" % (elapsed, start_time, end_time))

    dstat = dstat[(dstat['epoch'] >= start_time) & (dstat['epoch'] <= end_time)]

    lvldb.time = lvldb.time - start_time
    dstat.epoch = dstat.epoch - start_time

    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)

    ax.plot(dstat['epoch'], dstat['dsk/total:writ'], label="Disk writes")
    ax.plot(dstat['epoch'], dstat['dsk/total:read'], label="Disk reads")

    ax.plot(lvldb['time'], lvldb['data_written'], label='LevelDB writes')

    fig.legend()
    fig.savefig('dstat.pdf')

if __name__ == "__main__":
    main()
