#! /usr/bin/python3
'''
Runs db_bench, collects disk and CPU stats, and plots the data.
'''

from subprocess import Popen, call, DEVNULL, check_output, PIPE

import matplotlib.pyplot as plt
import pandas
import os
import argparse
import stats_analyser
import time
import signal
from threading import Timer
import sys
import numpy as np

# Make sure we store the db on the correct drive
DB_PATH = "./db_bench.data"
BINPATH = "./build"

BG_FNAME = "background_stats.csv"
DSTAT_FNAME = "dstat.csv"
LVLDB_FNAME = "foreground_stats.csv"
BG_COMPACTION_DATA_FNAME = "bg_compaction_data.csv"
MEMTABLE_COMPACTION_DATA_FNAME = "memtable_compaction_data.csv"
WORKLOAD = "writerandomburstsbytime"
DURATION = 100
BATCH_SIZE = 1000
VALUE_SIZE = 100
SYNC = True
BURST_LENGTH = 10
SLEEP_DURATION = 20
CGROUP_MEMORY_LIMIT = "200000000"
CGROUP_CPUS = "0-0"
CGROUP_WRITE_THRESHOLD = "8:32 200000000"
CGROUP_CPU_SHARE = "100" # A number from 0 to 1024: 1024 to allow complete CPU time
CPUS_RANGE = CGROUP_CPUS.split("-")
CPU_LIMIT = "100"
CPUS = [cpu for cpu in range(int(CPUS_RANGE[0]), int(CPUS_RANGE[-1])+1)]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", default=False)
    parser.add_argument("--plot", action="store_true", default=False)
    parser.add_argument("--cgroup", action="store_true", default=False)
    parser.add_argument("--run_all_exp", action="store_true", default=False)

    args = parser.parse_args()

    if args.run:
        run()

    if args.plot:
        plot()

    if args.cgroup:
        create_cgroup()

    if args.run_all_exp:
        run_all_exp()

    if args.plot or args.run or args.cgroup or args.run_all_exp:
        print("Done.")
    else:
        print("Warning: No option selected. Doing nothing.")

def create_cgroup():
    print("# Creating cgroup")
    call(["sudo", "cgcreate", "-g", "memory:ldb"])
    call(["sudo", "cgcreate", "-g", "cpu:ldb"])
    call(["sudo", "cgcreate", "-g", "blkio:ldb"])
    call(["sudo", "cgcreate", "-g", "cpuset:ldb"])
    os.system("echo " + CGROUP_MEMORY_LIMIT + " | sudo tee /sys/fs/cgroup/memory/ldb/memory.limit_in_bytes")
    os.system("echo " + CGROUP_CPUS + " | sudo tee /sys/fs/cgroup/cpuset/ldb/cpuset.cpus")
    os.system("echo 0 | sudo tee /sys/fs/cgroup/cpuset/ldb/cpuset.mems")
    os.system("echo \'" + CGROUP_WRITE_THRESHOLD + "\' | sudo tee /sys/fs/cgroup/blkio/ldb/blkio.throttle.write_bps_device")
    # os.system("echo " + CGROUP_CPU_SHARE + " | sudo tee /sys/fs/cgroup/cpu/ldb/cpu.shares")

def run_all_exp():
    f = open("all_exp.txt", "w")
    for cpu_limit in range(10, 100, 50):
        for disk_limit in range(50, 200, 100):
            os.system("echo \'" + "8:32 " + str(disk_limit) + "\' | sudo tee /sys/fs/cgroup/blkio/ldb/blkio.throttle.write_bps_device")
            os.system("sudo rm /users/nithinv/leveldb/db_bench.data/*")
            run(cpu_limit, disk_limit, f)
            print("run done")
    
    # fig = plt.figure()
    # ax = plt.axes(projection='3d')
    # ax.plot_surface(cpu_limits, disk_limits, throughputs,cmap='viridis', edgecolor='none')
    # ax.set_title('Surface plot')
    # plt.savefig("3d.png")

def run(cpu_limit = 100, disk_limit = 200, f=sys.stdout):
    print("# Loading data")
    call([BINPATH+"/db_bench", "--benchmarks=fillseq", "--use_existing_db=0", "--db="+DB_PATH])
    time.sleep(2)
    print("# Running Benchmark")
    if os.path.exists(DSTAT_FNAME):
        os.remove(DSTAT_FNAME) #dstat appends by default
    dstat = Popen(["dstat", "-C", ",".join(list(map(str, CPUS))) , "-gcdT", "--cpu-use", "--output="+DSTAT_FNAME], stdout=DEVNULL)
    print("Dstat initialized.")
    # "sudo", "cgexec", "-g", "memory,cpuset,blkio:ldb",
    dbbench = Popen(["sudo", "cgexec", "-g", "memory,cpuset,blkio:ldb", BINPATH+"/db_bench", "--benchmarks="+WORKLOAD, "--sleep_duration=%i"%SLEEP_DURATION, "--write_time_before_sleep=%i"%BURST_LENGTH,
        "--workload_duration=%i" % DURATION, "--db="+DB_PATH, "--use_existing_db=1", "--value_size=%i"%VALUE_SIZE, "--disk_write_limit=%i"%disk_limit, "--cpu_limit=%i"%cpu_limit], stdout=f)
        # "--sync=%i"%SYNC, "--batch_size=%i"%BATCH_SIZE])
    
    time.sleep(1)
    pid = check_output(["pidof", "-s", "db_bench"]).strip().decode("utf-8") 
    print(pid)
    print(dbbench.pid)
    cpulimit = Popen(["cpulimit", "-p", str(pid), "-l", str(cpu_limit)])

    # out, err = dbbench.communicate(timeout=DURATION + 5)
    # print(out)
    # throughput = float(out.decode("utf-8").split(" ")[-2].strip())
    # print(throughput)

    # try: 
    #     out, err = dbbench.communicate(timeout=DURATION + 5)
    #     print(out)
    #     throughput = float(out.decode("utf-8").split(" ")[-2].strip())
    #     print(throughput)
    # except:
    #     throughput = 0
    # dbbench.wait(timeout=DURATION+5)
    dbbench.wait(timeout=DURATION+5)
    cpulimit.kill()
    dstat.kill()

def format_compaction_data():
    input_file = os.path.join("db_bench.data", "LOG")
    output_file = os.path.join(os.getcwd(), BG_COMPACTION_DATA_FNAME)
    if os.path.exists(output_file):
        os.remove(output_file)
    stats_analyser.format_compaction_stats(input_file, output_file)
    output_file = os.path.join(os.getcwd(), MEMTABLE_COMPACTION_DATA_FNAME)
    if os.path.exists(output_file):
        os.remove(output_file)
    stats_analyser.format_memtable_compaction(input_file, output_file)

def plot():
    print("# Plotting")
    format_compaction_data()
    
    burst_times = pandas.read_csv("burst_times.csv", skipinitialspace=True)

    dstat = pandas.read_csv(DSTAT_FNAME, header=5)
    lvldb = pandas.read_csv(LVLDB_FNAME)
    bg = pandas.read_csv(BG_FNAME)
    bg_comp = pandas.read_csv(BG_COMPACTION_DATA_FNAME)
    mem_comp = pandas.read_csv(MEMTABLE_COMPACTION_DATA_FNAME)

    lvldb.time = lvldb.time / (1000*1000)
    bg.time = bg.time / (1000*1000)
    burst_times.start = burst_times.start / (1000*1000)
    burst_times.end = burst_times.end / (1000*1000)
    bg_comp.start_time = bg_comp.start_time / (1000*1000)
    bg_comp.end_time = bg_comp.end_time / (1000*1000)
    mem_comp.start_time = mem_comp.start_time / (1000*1000)
    mem_comp.end_time = mem_comp.end_time / (1000*1000)

    start_time = lvldb.time.min()
    end_time = lvldb.time.max()
    elapsed = int(end_time - start_time)

    print("Ran for %i seconds (%i to %i)" % (elapsed, start_time, end_time))

    dstat = dstat[(dstat['epoch'] >= start_time) & (dstat['epoch'] <= end_time)]
    bg = bg[(bg['time'] >= start_time) & (bg['time'] <= end_time)]
    bg_comp = bg_comp[(bg_comp['start_time'] >= start_time) & (bg_comp['end_time'] <= end_time)]
    mem_comp = mem_comp[(mem_comp['start_time'] >= start_time) & (mem_comp['end_time'] <= end_time)]

    bg.time = bg.time - start_time
    lvldb.time = lvldb.time - start_time
    dstat.epoch = dstat.epoch - start_time
    bg_comp.start_time = bg_comp.start_time - start_time
    bg_comp.end_time = bg_comp.end_time - start_time
    bg_comp["widths"] = bg_comp["end_time"] - bg_comp["start_time"]
    mem_comp.start_time = mem_comp.start_time - start_time 
    mem_comp.end_time = mem_comp.end_time - start_time
    mem_comp["widths"] = mem_comp["end_time"] - mem_comp["start_time"]
    # lvldb.loc[lvldb['time'] < 10, 'throughput'] = 0
    # dstat.loc[dstat['epoch'] < 10, 'writ'] = 0 
    # dstat.loc[dstat['epoch'] < 10, 'read'] = 0 

    def highlight_bursts(ax, elapsed):
        for _, row in burst_times.iterrows():
            ax.axvspan(row["start"] - start_time, row["end"] - start_time, alpha=0.25, lw=0)

    fig = plt.figure(figsize=(20,10))
    ax1 = fig.add_subplot(5, 1, 1)
    highlight_bursts(ax1, elapsed)

    # Dstat reports in kB while leveldb does in bytes
    print(len(dstat['writ']))
    print(len(dstat['epoch']))
    ax1.plot(dstat['epoch'], dstat['writ'] / (1024*1024), label="Disk writes")
    ax1.plot(dstat['epoch'], dstat['read'] / (1024*1024), label="Disk reads")
    ax1.plot(lvldb['time'], lvldb['throughput'] / (1024*1024), label='LevelDB writes')
    ax1.set_ylabel('Throughput (MB/s)')
    ax1.legend()

    ax2 = fig.add_subplot(5, 1, 2)
    highlight_bursts(ax2, elapsed)
    level_data = {-1: [(i) for i in bg["memoryUsage"]]}

    for (epoch_num, level_str) in enumerate(bg.levelWiseData):
        if level_str == "":
            raise RuntimeError("Cannot handle data")

        for substr in level_str.split('::'):
            if substr == "":
                continue

            level_num, _, size, _, _, _ = substr.split(':')

            level_num = int(level_num)
            size = float(size)

            if level_num not in level_data:
                level_data[level_num] = []

                # make sure the alignment is correct
                for _ in range(epoch_num):
                    level_data[level_num].append(0)

            level_data[level_num].append(size)

    labels = []
    sizes = []

    for num, size in sorted(level_data.items(), key=lambda item: item[0]):
        label = "Memtable" if num < 0 else "Level %i" %num
        labels.append(label)
        sizes.append(size)

    ax2.stackplot(bg['time'], sizes, labels=labels)
    ax2.set_ylabel('Size (Mb)')
    ax2.legend()

    ax3 = fig.add_subplot(5, 1, 3)
    highlight_bursts(ax3, elapsed)

    cpus = CGROUP_CPUS.split("-")
    for cpu in range(int(cpus[0]), int(cpus[-1])+1):
        ax3.plot(dstat['epoch'], dstat[str(cpu)], label="CPU #%i"%cpu)

    # pos = 0
    # while True:
    #     #did we enumerate all cores?
    #     if str(pos) not in dstat.columns:
    #         break

    #     ax3.plot(dstat['epoch'], dstat[str(pos)], label="CPU #%i"%pos)
    #     pos += 1

    # print("Found %i CPU cores" % pos)

    ax3.set_ylabel('CPU Usage (%)')
    # ax3.legend()

    ax4 = fig.add_subplot(5, 1, 4)
    highlight_bursts(ax4, elapsed)

    # for cpu in CPUS:
    #     for name in ["usr", "sys"]:
    #         name = "cpu" + str(cpu) + " usage:" + name
    #         ax4.plot(dstat['epoch'], dstat[name], label=name)

    # print("Found %i CPU cores" % pos)
    colors = {0:'orange', 1:'green', 2:'red', 3:'purple'}
    labels = {0:'Level 0 to Level 1', 1:'Level 1 to Level 2', 2:'Level 2 to Level 3', 3:'Level 3 to Level 4'}
    levels = bg_comp['level']
    bg_comp['colors'] = pandas.Series([colors[level] for level in levels])
    bg_comp['labels'] = pandas.Series([labels[level] for level in levels])
    for level in set(bg_comp['level']):
        data = bg_comp[bg_comp['level'] == level]
        x, y, widths = data['start_time'], data['data_written'], data['widths']
        color, label = colors[level], labels[level]
        ax4.bar(x, y, width=widths, color=color, label=label, align='edge')
    # ax4.bar(bg_comp['start_time'], bg_comp['data_read'], width=bg_comp['widths'], color=bg_comp['colors'], align="edge" label="Data read")
    # ax4.bar(bg_comp['start_time'], bg_comp['data_written'], width=bg_comp['widths'], color=bg_comp['colors'], label={'orange':'Level 0', 'green':'Level 1', 'red':'Level 2', 'purple':'Level 3'}, align='edge')
    # ax4.bar(mem_comp['start_time'], mem_comp['data_written'], width=mem_comp['widths'], align='edge', label="Memtable data written")
    
    ax4.legend()
    
    ax4.set_ylabel('BG Compaction \n data written (MB)')
    ax4.set_xlabel('Time (seconds)')
    ax4.set_xticks(np.arange(0, 125, 20.0))

    ax5 = fig.add_subplot(5, 1, 5)
    highlight_bursts(ax5, elapsed)
    ax5.bar(mem_comp['start_time'], mem_comp['data_written'] / (1024*1024), width=mem_comp['widths'], align='edge', label="Memtable data written")
    ax5.set_ylabel('Compaction memtable \n data written (MB)')
    ax5.set_xlabel('Time (seconds)')
    ax5.set_xticks(np.arange(0, 125, 20.0))

    fig.savefig('dstat.pdf')

if __name__ == "__main__":
    main()
