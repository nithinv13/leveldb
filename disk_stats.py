#! /usr/bin/python3
'''
Runs db_bench, collects disk and CPU stats, and plots the data.
'''

from subprocess import Popen, call, DEVNULL, check_output

import matplotlib.pyplot as plt
import pandas
import os
import argparse
import stats_analyser

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
BURST_LENGTH = 5
SLEEP_DURATION = 10
CGROUP_MEMORY_LIMIT = "200000000"
CGROUP_CPUS = "0-0"
CGROUP_WRITE_THRESHOLD = "8:32 200000000"
CGROUP_CPU_SHARE = "100" # A number from 0 to 1024: 1024 to allow complete CPU time
CPUS_RANGE = CGROUP_CPUS.split("-")
CPUS = [cpu for cpu in range(int(CPUS_RANGE[0]), int(CPUS_RANGE[-1])+1)]

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
    os.system("echo " + CGROUP_MEMORY_LIMIT + " | sudo tee /sys/fs/cgroup/memory/ldb/memory.limit_in_bytes")
    os.system("echo " + CGROUP_CPUS + " | sudo tee /sys/fs/cgroup/cpuset/ldb/cpuset.cpus")
    os.system("echo 0 | sudo tee /sys/fs/cgroup/cpuset/ldb/cpuset.mems")
    os.system("echo \'" + CGROUP_WRITE_THRESHOLD + "\' | sudo tee /sys/fs/cgroup/blkio/ldb/blkio.throttle.write_bps_device")
    # os.system("echo " + CGROUP_CPU_SHARE + " | sudo tee /sys/fs/cgroup/cpu/ldb/cpu.shares")

def run():
    print("# Loading data")
    call([BINPATH+"/db_bench", "--benchmarks=fillseq", "--use_existing_db=0", "--db="+DB_PATH])

    print("# Running Benchmark")
    if os.path.exists(DSTAT_FNAME):
        os.remove(DSTAT_FNAME) #dstat appends by default
    dstat = Popen(["dstat", "-C", ",".join(list(map(str, CPUS))) , "-gcdT", "--cpu-use", "--output="+DSTAT_FNAME], stdout=DEVNULL)
    print("Dstat initialized.")

    dbbench = Popen([BINPATH+"/db_bench", "--benchmarks="+WORKLOAD, "--sleep_duration=%i"%SLEEP_DURATION, "--write_time_before_sleep=%i"%BURST_LENGTH,
        "--workload_duration=%i" % DURATION, "--db="+DB_PATH, "--use_existing_db=1", "--value_size=%i"%VALUE_SIZE])
        # "--sync=%i"%SYNC, "--batch_size=%i"%BATCH_SIZE])
    
    pid = check_output(["pidof", "-s", "db_bench"]).strip().decode("utf-8") 
    cpulimit = Popen(["cpulimit", "-p", str(pid), "-l", str(10)])
    print(pid)

    dbbench.wait()
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

    fig = plt.figure(figsize=(16,10))
    ax1 = fig.add_subplot(4, 1, 1)
    highlight_bursts(ax1, elapsed)

    # Dstat reports in kB while leveldb does in bytes
    print(dstat['writ'])
    print(lvldb['throughput'])
    ax1.plot(dstat['epoch'], dstat['writ'], label="Disk writes")
    ax1.plot(dstat['epoch'], dstat['read'], label="Disk reads")
    ax1.plot(lvldb['time'], lvldb['throughput'], label='LevelDB writes')

    ax1.set_ylabel('Throughput (B/s)')
    #ax1.set_xlabel('Time (seconds)')

    ax1.legend()

    ax2 = fig.add_subplot(4, 1, 2)
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

    ax3 = fig.add_subplot(4, 1, 3)
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
    ax3.legend()

    ax4 = fig.add_subplot(4, 1, 4)
    highlight_bursts(ax4, elapsed)

    # for cpu in CPUS:
    #     for name in ["usr", "sys"]:
    #         name = "cpu" + str(cpu) + " usage:" + name
    #         ax4.plot(dstat['epoch'], dstat[name], label=name)

    # print("Found %i CPU cores" % pos)
    colors = {0:'orange', 1:'green', 2:'red', 3:'purple'}
    levels = bg_comp['level']
    bg_comp['colors'] = pandas.Series([colors[level] for level in levels])
    # ax4.bar(bg_comp['start_time'], bg_comp['data_read'], width=bg_comp['widths'], color=bg_comp['colors'], align="edge" label="Data read")
    # ax4.bar(mem_comp['start_time'], mem_comp['data_written'], width=mem_comp['widths'], align='edge', label="Memtable data written")
    ax4.bar(bg_comp['start_time'], bg_comp['data_written'], width=bg_comp['widths'], color=bg_comp['colors'], align='edge', label="Data written")
    ax4.legend()
    
    ax4.set_ylabel('Data written (MB)')
    ax4.legend()
    ax4.set_xlabel('Time (seconds)')


    fig.savefig('dstat.pdf')

def plot_compaction_data(input_file, total_time):
    with open(input_file) as f:
        lines = f.readlines()
        header = lines[0].rstrip("\n").split(",")
        colors = ["0.9", "0.6", "0.3", "0.05"]
        total_data_read = 0 
        total_data_written = 0
        x, color_list = [], []
        y_read, y_written = [], []
        y_read_total, y_written_total = [], []
        widths = []
        minx = float(lines[1][2])
        for line in lines[1:]:
            line = line.split(",")
            x.append(float(line[header.index("start_time")]) + minx)
            level = int(line[header.index("level")])
            data_read, data_written = float(line[header.index("data_read")]), float(line[header.index("data_written")])
            total_data_read += data_read
            total_data_written += data_written
            y_read.append(data_read)
            y_written.append(data_written)
            y_read_total.append(total_data_read)
            y_written_total.append(total_data_written)
            color_list.append(colors[level])
            widths.append(float(line[header.index("end_time")])-float(line[header.index("start_time")]))
        
        # fig = initialize_fig()
        # plot(x, y_read_total, "time", "Total compaction data read (MB)", HOME + "/compaction_graphs/compaction_data_read_total.png", \
        #     color_list, widths, 10, 100)
        # plot(x, y_written_total, "time", "Total compaction data written (MB)", HOME + "/compaction_graphs/compaction_data_written_total.png", \
        #     color_list, widths, 10, 100)
        plot(x, y_read, "time", "Compaction data read (MB)", HOME + "/compaction_graphs/compaction_data_read.png", \
            color_list, widths, 10, 100)
        plot(x, y_written, "time", "Compaction data written (MB)", HOME + "/compaction_graphs/compaction_data_written.png", \
            color_list, widths, 10, 100)
        ax1 = special_plot(fig, x, y_read, "time", "Compaction data \n read (MB)", color_list, widths, 10, 200, 311)
        ax2 = special_plot(fig, x, y_written, "time", "Compaction data \n written (MB)", color_list, widths, 10, 200, 312)
        x_data, y_data = plotter("./build/foreground_stats.csv", "time", "data_written", HOME + "/graphs/data_written" + extra + ".png", "time", "Total data written (MB)", ret=True)
        ax3 = special_plot(fig, x_data, y_data, "time", "Total data \n written", None, None, 10, 200, 313)
        plt.subplot(ax1)
        plt.subplot(ax2)
        plt.subplot(ax3)
        plt.savefig(HOME + "/graphs/tester.png")


if __name__ == "__main__":
    main()
