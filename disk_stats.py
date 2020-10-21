#! /usr/bin/python3

from subprocess import Popen, call, DEVNULL

import matplotlib.pyplot as plt
import pandas
import os
import argparse

# Make sure we store the db on the correct drive
DB_PATH = "./db_bench.data"
BINPATH = "./build"

BG_FNAME = "background_stats.csv"
DSTAT_FNAME = "dstat.csv"
LVLDB_FNAME = "foreground_stats.csv"
WORKLOAD = "writerandomburstsbytime"
DURATION = 200

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
    print("# Loading data")
    call([BINPATH+"/db_bench", "--benchmarks=fillseq", "--use_existing_db=0"])

    print("# Running Benchmark")
    if os.path.exists(DSTAT_FNAME):
        os.remove(DSTAT_FNAME) #dstat appends by default
    dstat = Popen(["dstat", "-gdT", "--output="+DSTAT_FNAME], stdout=DEVNULL)
    print("Dstat initialized.")

    call([BINPATH+"/db_bench", "--benchmarks="+WORKLOAD, "--sleep_duration=10", "--write_time_before_sleep=5", "--workload_duration=%i" % DURATION, "--db="+DB_PATH, "--use_existing_db=1"])

    dstat.kill()

def plot():
    print("# Plotting")

    dstat = pandas.read_csv(DSTAT_FNAME, header=5)
    lvldb = pandas.read_csv(LVLDB_FNAME)
    bg = pandas.read_csv(BG_FNAME)

    lvldb.time = lvldb.time / (1000*1000)
    bg.time = bg.time / (1000*1000)

    start_time = lvldb.time.min()
    end_time = lvldb.time.max()
    elapsed = int(end_time - start_time)

    print("Ran for %i seconds (%i to %i)" % (elapsed, start_time, end_time))

    dstat = dstat[(dstat['epoch'] >= start_time) & (dstat['epoch'] <= end_time)]
    bg = bg[(bg['time'] >= start_time) & (bg['time'] <= end_time)]

    bg.time = bg.time - start_time
    lvldb.time = lvldb.time - start_time
    dstat.epoch = dstat.epoch - start_time

    fig = plt.figure()
    ax1 = fig.add_subplot(2,1,1)

    # Dstat reports in kB while leveldb does in bytes
    ax1.plot(dstat['epoch'], dstat['dsk/total:writ'], label="Disk writes")
    ax1.plot(dstat['epoch'], dstat['dsk/total:read'], label="Disk reads")
    ax1.plot(lvldb['time'], lvldb['throughput'] / 1000.0, label='LevelDB writes')

    ax1.set_ylabel('Throughput (kb/s)')
    #ax1.set_xlabel('Time (seconds)')

    ax1.legend()

    ax2 = fig.add_subplot(2,1,2)
    level_data = {}

    for (epoch_num, level_str) in enumerate(bg.levelWiseData):
        if level_str == "":
            raise RuntimeError("Cannot handle data")

        for substr in level_str.split('::'):
            if substr == "":
                continue

            level_num, num_files, size, _, _, _ = substr.split(':')

            level_num = int(level_num)
            size = float(size)

            if level_num not in level_data:
                level_data[level_num] = []

                # make sure the alignment is correct
                for _ in range(epoch_num):
                    level_data[level_num].append(0)

            level_data[level_num].append(size)

    labels = ["Level %i" %num for num in level_data.keys()]
    sizes = level_data.values()

    ax2.stackplot(bg['time'], sizes, labels=labels)

    ax2.set_ylabel('Size (Mb)')
    ax2.set_xlabel('Time (seconds)')

    ax2.legend()

    fig.savefig('dstat.pdf')

if __name__ == "__main__":
    main()
