#! /usr/bin/python3

from subprocess import Popen, call, DEVNULL

import matplotlib
import pandas
import os

# Make sure we store the db on the correct drive
DB_PATH="./db_bench_data"
BINPATH="./build"

DSTAT_FNAME = "dstat.csv"
LVLDB_FNAME = "foreground_stats.csv"
WORKLOAD = "writerandomburstsbytime"

def main():
    #run()
    plot()
    print("DONE")

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

    start_time = int(lvldb.time.min() / (1000*1000))
    end_time = int(lvldb.time.max() / (1000*1000))
    elapsed = end_time - start_time

    print("Ran for %i seconds (%i to %i)" % (elapsed, start_time, end_time))

    dstat = dstat[(dstat['epoch'] >= start_time) & (dstat['epoch'] <= end_time)]

if __name__ == "__main__":
    main()
