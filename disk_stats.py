#! /usr/bin/python3
'''
Runs db_bench, collects disk and CPU stats, and plots the data.
'''

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
DURATION = 100
BATCH_SIZE = 1000
SYNC = 1
BURST_LENGTH = 5
SLEEP_DURATION = 10
CGROUP_MEMORY_LIMIT = 50000000
CGROUP_CPUS = "0-2"
CGROUP_WRITE_THRESHOLD = 50000000

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", default=False)
    parser.add_argument("--plot", action="store_true", default=False)
    parser.add_argument("--cgroup", action="store_true", default=False)

    args = parser.parse_args()

    if args.run:
        run()

    if args.plot:
        plot()

    if args.cgroup:
        create_cgroup()

    if args.plot or args.run or args.cgroup:
        print("Done.")
    else:
        print("Warning: No option selected. Doing nothing.")

def create_cgroup():
    print("# Creating cgroup")
    call(["sudo", "cgcreate", "-g", "memory:ldb"])
    call(["sudo", "cgcreate", "-g", "cpu:ldb"])
    call(["sudo", "cgcreate", "-g", "blkio:ldb"])
    call(["sudo", "cgcreate", "-g", "cpuset:ldb"])
    os.system("echo 50000000 | sudo tee /sys/fs/cgroup/memory/ldb/memory.limit_in_bytes")
    os.system("echo 0-2 | sudo tee /sys/fs/cgroup/cpuset/ldb/cpuset.cpus")
    os.system("echo 0 | sudo tee /sys/fs/cgroup/cpuset/ldb/cpuset.mems")
    os.system("echo \'8:32 10000000\' | sudo tee /sys/fs/cgroup/blkio/ldb/blkio.throttle.write_bps_device")
    # call(["echo", "50000000", "|", "sudo", "tee", "/sys/fs/cgroup/memory/ldb/memory.limit_in_bytes"])
    # call(["echo", "0-4", "|", "sudo", "tee", "/sys/fs/cgroup/cpuset/ldb/cpuset.cpus"])
    # call(["echo", "8:32 40000000", "|", "sudo", "tee", "/sys/fs/cgroup/blkio/ldb/blkio.throttle.write_bps_device"])
    # call(["echo", "8:0 40000000", "|", "sudo", "tee", "/sys/fs/cgroup/cpuset/ldb/blkio.throttle.write_bps_device"]) # Use this for HDD

def run():
    print("# Loading data")
    call([BINPATH+"/db_bench", "--benchmarks=fillseq", "--use_existing_db=0", "--db="+DB_PATH])

    print("# Running Benchmark")
    if os.path.exists(DSTAT_FNAME):
        os.remove(DSTAT_FNAME) #dstat appends by default
    dstat = Popen(["dstat", "-gcdT", "--cpu-use", "--output="+DSTAT_FNAME], stdout=DEVNULL)
    print("Dstat initialized.")

    call([BINPATH+"/db_bench", "--benchmarks="+WORKLOAD, "--sleep_duration=%i"%SLEEP_DURATION, "--write_time_before_sleep=%i"%BURST_LENGTH, "--workload_duration=%i" % DURATION, "--db="+DB_PATH, "--use_existing_db=1"])
    #, "--sync=%i"%SYNC)--batch_size=%i"%BATCH_SIZE])

    dstat.kill()

def plot():
    print("# Plotting")
    burst_times = pandas.read_csv("burst_times.csv", skipinitialspace=True)

    dstat = pandas.read_csv(DSTAT_FNAME, header=5)
    lvldb = pandas.read_csv(LVLDB_FNAME)
    bg = pandas.read_csv(BG_FNAME)

    lvldb.time = lvldb.time / (1000*1000)
    bg.time = bg.time / (1000*1000)
    burst_times.start = burst_times.start / (1000*1000)
    burst_times.end = burst_times.end / (1000*1000)

    start_time = lvldb.time.min()
    end_time = lvldb.time.max()
    elapsed = int(end_time - start_time)

    print("Ran for %i seconds (%i to %i)" % (elapsed, start_time, end_time))

    dstat = dstat[(dstat['epoch'] >= start_time) & (dstat['epoch'] <= end_time)]
    bg = bg[(bg['time'] >= start_time) & (bg['time'] <= end_time)]

    bg.time = bg.time - start_time
    lvldb.time = lvldb.time - start_time
    dstat.epoch = dstat.epoch - start_time

    def highlight_bursts(ax, elapsed):
        for _, row in burst_times.iterrows():
            ax.axvspan(row["start"] - start_time, row["end"] - start_time, alpha=0.25, lw=0)

    fig = plt.figure(figsize=(16,10))
    ax1 = fig.add_subplot(4, 1, 1)
    highlight_bursts(ax1, elapsed)

    # Dstat reports in kB while leveldb does in bytes
    print(dstat['writ'])
    print(lvldb['throughput'])
    ax1.plot(dstat['epoch'], dstat['writ'], label="Disk writes")
    ax1.plot(dstat['epoch'], dstat['read'], label="Disk reads")
    ax1.plot(lvldb['time'], lvldb['throughput'], label='LevelDB writes')

    ax1.set_ylabel('Throughput (Kb/s)')
    #ax1.set_xlabel('Time (seconds)')

    ax1.legend()

    ax2 = fig.add_subplot(4, 1, 2)
    highlight_bursts(ax2, elapsed)
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

    labels = ["Level %i" %num for num in level_data]
    sizes = level_data.values()

    ax2.stackplot(bg['time'], sizes, labels=labels)

    ax2.set_ylabel('Size (Mb)')
    ax2.legend()

    ax3 = fig.add_subplot(4, 1, 3)
    highlight_bursts(ax3, elapsed)
    pos = 0
    while True:
        #did we enumerate all cores?
        if str(pos) not in dstat.columns:
            break

        ax3.plot(dstat['epoch'], dstat[str(pos)], label="CPU #%i"%pos)
        pos += 1

    print("Found %i CPU cores" % pos)

    ax3.set_ylabel('CPU Usage (%)')
    ax3.legend()

    ax4 = fig.add_subplot(4, 1, 4)
    highlight_bursts(ax4, elapsed)

    for name in ["idl", "usr", "sys"]:
        ax4.plot(dstat['epoch'], dstat[name], label=name)

    print("Found %i CPU cores" % pos)

    ax4.set_ylabel('CPU Usage (%)')
    ax4.legend()
    ax4.set_xlabel('Time (seconds)')


    fig.savefig('dstat.pdf')

if __name__ == "__main__":
    main()
