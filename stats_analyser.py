import csv
import math
import numpy as np
import matplotlib.pyplot as plt

def parse(input, y, only_level0):
    header = ["level", "files", "size", "time", "reads", "writes"]
    y = y.split("::")[1]
    if not input:
        return 0
    rows = input.split("::")
    if len(rows) == 0:
        return 0
    for i in range(len(rows)):
        rows[i] = rows[i].split(":")
    if only_level0:
        return rows[0][header.index(y)]
    total = 0
    col = header.index(y)
    length = len(header)
    for i in range(len(rows)):
        if len(rows[i]) != length:
            continue
        total += float(rows[i][col])
    return total

def plotter(file_name, x, y, output_file, x_label, y_label, only_level0 = False, total=False, ret=False):
    start_time = 0
    if "background" in file_name:
        start_time_file = "build/foreground_stats.csv"
    else:
        start_time_file = "build/background_stats.csv"
    with open(start_time_file) as f:
        csv_reader = csv.reader(f, delimiter=',')
        csv_reader = list(csv_reader)
        start_time = float(csv_reader[1][0])

    with open(file_name) as f:
        csv_reader = csv.reader(f, delimiter=',')
        csv_reader = list(csv_reader)
        header = csv_reader[0]
        prev_val = 0
        start_time = min(start_time, float(csv_reader[1][0]))
        x_list = []
        y_list = []
        total_val = 0
        for row in csv_reader[1:]:
            time = (float(row[header.index(x)]) - start_time) / 10**6
            if y.startswith("levelWiseData"):
                y_val = parse(row[header.index("levelWiseData")], y, only_level0)
                temp = y_val 
                y_val = y_val - prev_val 
                prev_val = temp
            else:
                y_val = float(row[header.index(y)])
                # if total: 
                #     total_val += y_val 
                # else:
                #     total_val = y_val
            x_list.append(time)
            y_list.append(y_val)
    
    if ret:
        return x_list, y_list

    plt.bar(x_list, y_list)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.savefig(output_file)
    plt.clf()
        

def get_time_diff(start, end):
    import datetime
    start_obj = datetime.datetime.strptime(start, '%Y/%m/%d-%H:%M:%S.%f')   
    end_obj = datetime.datetime.strptime(end, '%Y/%m/%d-%H:%M:%S.%f')
    diff = end_obj - start_obj 
    tuple = divmod(diff.total_seconds(), 60)
    return float(tuple[0])*60 + float(tuple[1])

def format_compaction_stats(file_name, output_file):
    header = ["compaction_no", "level", "start_time", "end_time", "version_summary_before", "compacting", "compacted", \
        "version_summary_after", "data_read", "data_written"]
    workload_start = 0
    compaction_no = 1
    row = ["None" for _ in range(len(header))]
    row[0] = str(compaction_no)
    with open(output_file, 'w') as out_file:
        out_file.write(",".join(header) + "\n")
        with open(file_name) as f:
            lines = f.readlines()
            workload_start = lines[0].split()[0]
            for line in lines:
                cols = line.split(" ")
                if "Compacting" in line:
                    start_time = cols[0]
                    level = int(cols[3][-1])
                    row[header.index("start_time")] = str(get_time_diff(workload_start, start_time))
                    row[header.index("level")] = str(level)
                    row[header.index("compacting")] = str(cols[3] + "+" + cols[5])
                elif "Version summary" in line:
                    row[header.index("version_summary_before")] = line.split(": ")[-1].rstrip("\n")
                elif "Compaction stats" in line:
                    row[header.index("data_read")] = str(float(cols[4]) / (1024*1024))
                    row[header.index("data_written")] = str(float(cols[6]) / (1024*1024))
                elif "Compacted" in line:
                    row[header.index("compacted")] = str(cols[3] + "+" + cols[5])
                elif "compacted to" in line:
                    end_time = cols[0]
                    row[header.index("end_time")] = str(get_time_diff(workload_start, end_time))
                    row[header.index("version_summary_after")] = line.split(": ")[-1].rstrip("\n")
                    out_file.write(",".join(row) + "\n")
                    compaction_no += 1
                    row = ["None" for _ in range(len(header))]
                    row[0] = str(compaction_no)

def plot(x, y, x_title, y_title, output_file, color_list, widths, x_tick, y_tick):
    plt.bar(x, y, color=color_list, width=widths, align="edge")
    #plt.legend()
    plt.xlabel(x_title)
    plt.ylabel(y_title)
    plt.xticks(np.arange(0, max(x)+1, x_tick))
    plt.yticks(np.arange(0, max(y)+1, y_tick))
    plt.savefig(output_file)
    plt.clf()


def initialize_fig():
    fig = plt.figure()
    return fig

def save_fig(output_file):
    plt.savefig(output_file)
    plt.clf()

def special_plot(fig, x, y, x_title, y_title, color_list, widths, x_tick, y_tick, position):
    # fig = plt.figure()
    #ax1 = fig.add_subplot(position)
<<<<<<< HEAD
=======
    
    
>>>>>>> cce843a00de9ab57f2ee2d06b6803c7a075aa0f5
    ax = plt.subplot(position)
    if widths:
        ax.bar(x, y, color=color_list, width=widths, align="edge")
    else:
        ax.bar(x, y)
    ax.set_ylabel(y_title)
<<<<<<< HEAD
=======
    plt.ylim(0, 1100)
    plt.xticks(np.arange(0, 120+1, step=x_tick))
    plt.yticks(np.arange(0, max(y)+1, step=y_tick))
>>>>>>> cce843a00de9ab57f2ee2d06b6803c7a075aa0f5
    # plt.savefig(HOME + "/graphs/tester2.png")
    return ax

def plot_compaction_data(input_file, total_time):
    with open(input_file) as f:
        lines = f.readlines()
        header = lines[0].rstrip("\n").split(",")
        for line in lines[1:]:
            line = line.split(",")
            level = int(line[header.index("level")])
            start_time = float(line[header.index("start_time")])
            end_time = float(line[header.index("end_time")])
            plt.axhline(y = level, xmin = start_time / total_time, xmax = end_time / total_time, color = "r")
        plt.xticks(np.arange(0.0, total_time, 10))
        plt.yticks(np.arange(-1, 8, 1))
        plt.xlabel("time")
        plt.ylabel("level")
        plt.savefig(HOME + "/compaction_graphs/level_wise_compaction.png")
        plt.clf()
        colors = ["0.9", "0.6", "0.3", "0.05"]
        print(header)
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
        
        fig = initialize_fig()
        plot(x, y_read_total, "time", "Total compaction data read (MB)", HOME + "/compaction_graphs/compaction_data_read_total.png", \
<<<<<<< HEAD
            color_list, widths, 10, 100)
        plot(x, y_written_total, "time", "Total compaction data written (MB)", HOME + "/compaction_graphs/compaction_data_written_total.png", \
            color_list, widths, 10, 100)
        plot(x, y_read, "time", "Compaction data read (MB)", HOME + "/compaction_graphs/compaction_data_read.png", \
            color_list, widths, 10, 10)
        plot(x, y_written, "time", "Compaction data written (MB)", HOME + "/compaction_graphs/compaction_data_written.png", \
            color_list, widths, 10, 10)
        ax1 = special_plot(fig, x, y_read, "time", "Compaction data read (MB)", color_list, widths, 10, 10, 311)
        ax2 = special_plot(fig, x, y_written, "time", "Compaction data written (MB)", color_list, widths, 10, 10, 312)
        x_data, y_data = plotter("./build/foreground_stats.csv", "time", "data_written", HOME + "/graphs/data_written" + extra + ".png", "time", "Total data written (MB)", ret=True)
        ax3 = special_plot(fig, x_data, y_data, "time", "Total data written", None, None, 10, 100, 313)
=======
            color_list, widths, 10, 100)
        plot(x, y_written_total, "time", "Total compaction data written (MB)", HOME + "/compaction_graphs/compaction_data_written_total.png", \
            color_list, widths, 10, 100)
        plot(x, y_read, "time", "Compaction data read (MB)", HOME + "/compaction_graphs/compaction_data_read.png", \
            color_list, widths, 10, 100)
        plot(x, y_written, "time", "Compaction data written (MB)", HOME + "/compaction_graphs/compaction_data_written.png", \
            color_list, widths, 10, 100)
        ax1 = special_plot(fig, x, y_read, "time", "Compaction data \n read (MB)", color_list, widths, 10, 200, 311)
        ax2 = special_plot(fig, x, y_written, "time", "Compaction data \n written (MB)", color_list, widths, 10, 200, 312)
        x_data, y_data = plotter("./build/foreground_stats.csv", "time", "data_written", HOME + "/graphs/data_written" + extra + ".png", "time", "Total data written (MB)", ret=True)
        ax3 = special_plot(fig, x_data, y_data, "time", "Total data \n written", None, None, 10, 200, 313)
>>>>>>> cce843a00de9ab57f2ee2d06b6803c7a075aa0f5
        plt.subplot(ax1)
        plt.subplot(ax2)
        plt.subplot(ax3)
        plt.savefig(HOME + "/graphs/tester.png")

def plot_cdf(file_name, column):
    data = []
    with open(HOME + "/test.csv") as f:
        lines = f.readlines()
        for line in lines[1:]:
            line = line.split(",")
            data_point = float(line[3])-float(line[2])
            data.append(data_point)
    
    num_bins = 40
    counts, bin_edges = np.histogram (data, bins=num_bins, normed=True)
    cdf = np.cumsum(counts)
    plt.plot(bin_edges[1:], cdf/cdf[-1])
    plt.xlabel("compaction time (s)")
    plt.ylabel("Probability")
    plt.savefig(HOME + "/compaction_graphs/compaction_time_cdf.png")
    plt.clf()
    plt.hist(data, bins=40, label=len(data))
    plt.legend()
    plt.xlabel("Time for compaction (s)")
    plt.ylabel("Count of compactions")
    plt.savefig(HOME + "/compaction_graphs/compaction_time_pdf.png")
    plt.clf()


if __name__ == "__main__":
<<<<<<< HEAD
    HOME = "/users/nithinv"
    extra = ""
    # plotter("./build/background_stats.csv", "time", "memoryUsage", HOME + "/graphs/memory" + extra + ".png", "time", "Memory usage (MB)")
    # plotter("./build/background_stats.csv", "time", "compactionScheduledCount", HOME + "/graphs/compaction" + extra + ".png", "time", "Number of compactions scheduled")
    # plotter("./build/background_stats.csv", "time", "levelWiseData::writes", HOME + "/graphs/compaction_writes" + extra + ".png", "time", "Compaction writes (MB)")
    # plotter("./build/background_stats.csv", "time", "levelWiseData::reads", HOME + "/graphs/compaction_reads" + extra + ".png", "time", "Compaction reads (MB)")
    # plotter("./build/background_stats.csv", "time", "levelWiseData::files", HOME + "/graphs/files_created" + extra + ".png", "time", "Number of files created in the interval")
    # plotter("./build/background_stats.csv", "time", "levelWiseData::time", HOME + "/graphs/compaction_time" + extra + ".png", "time", "Compaction time (s)")
    # plotter("./build/background_stats.csv", "time", "writeBufferSize", HOME + "/graphs/write_buffer_size" + extra + ".png", "time", "Write buffer size (MB)")
    # plotter("./build/foreground_stats.csv", "time", "writes", HOME + "/graphs/writes" + extra + ".png", "time", "Number of writes in the interval")
    # plotter("./build/foreground_stats.csv", "time", "throughput", HOME + "/graphs/throughput" + extra + ".png", "time", "Throughput in the interval (MB/s)")
    # #plotter("./build/foreground_stats.csv", "time", "writes", HOME + "/graphs/writes1" + extra + ".png", "time", "Total write data (MB)", True)
    # plotter("./build/foreground_stats.csv", "time", "data_written", HOME + "/graphs/data_written" + extra + ".png", "time", "Total data written (MB)")
    # format_compaction_stats('/tmp/leveldbtest-20001/dbbench/LOG', HOME + '/test.csv')
=======
    HOME = "/users/arijitx/leveldb"
    extra = ""
    plotter("./build/background_stats.csv", "time", "memoryUsage", HOME + "/graphs/memory" + extra + ".png", "time", "Memory usage (MB)")
    plotter("./build/background_stats.csv", "time", "compactionScheduledCount", HOME + "/graphs/compaction" + extra + ".png", "time", "Number of compactions scheduled")
    plotter("./build/background_stats.csv", "time", "levelWiseData::writes", HOME + "/graphs/compaction_writes" + extra + ".png", "time", "Compaction writes (MB)")
    plotter("./build/background_stats.csv", "time", "levelWiseData::reads", HOME + "/graphs/compaction_reads" + extra + ".png", "time", "Compaction reads (MB)")
    plotter("./build/background_stats.csv", "time", "levelWiseData::files", HOME + "/graphs/files_created" + extra + ".png", "time", "Number of files created in the interval")
    plotter("./build/background_stats.csv", "time", "levelWiseData::time", HOME + "/graphs/compaction_time" + extra + ".png", "time", "Compaction time (s)")
    plotter("./build/background_stats.csv", "time", "writeBufferSize", HOME + "/graphs/write_buffer_size" + extra + ".png", "time", "Write buffer size (MB)")
    plotter("./build/background_stats.csv", "time", "MemTableSize", HOME + "/graphs/memtable_size" + extra + ".png", "time", "Memtable size (MB)")
    plotter("./build/foreground_stats.csv", "time", "writes", HOME + "/graphs/writes" + extra + ".png", "time", "Number of writes in the interval")
    plotter("./build/foreground_stats.csv", "time", "throughput", HOME + "/graphs/throughput" + extra + ".png", "time", "Throughput in the interval (MB/s)")
    #plotter("./build/foreground_stats.csv", "time", "writes", HOME + "/graphs/writes1" + extra + ".png", "time", "Total write data (MB)", True)
    plotter("./build/foreground_stats.csv", "time", "data_written", HOME + "/graphs/data_written" + extra + ".png", "time", "Total data written (MB)")
    format_compaction_stats('/tmp/leveldbtest-20001/dbbench/LOG', HOME + '/test.csv')
>>>>>>> cce843a00de9ab57f2ee2d06b6803c7a075aa0f5
    plot_compaction_data(HOME + "/test.csv", 100)
    # plot_cdf("", "")
    # plot_test()