import csv
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

def plotter(file_name, x, y, output_file, x_label, y_label, only_level0 = False):
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
        for row in csv_reader[1:]:
            time = (float(row[header.index(x)]) - start_time) / 10**6
            if y.startswith("levelWiseData"):
                y_val = parse(row[header.index("levelWiseData")], y, only_level0)
                temp = y_val 
                y_val = y_val - prev_val 
                prev_val = temp
            else:
                y_val = float(row[header.index(y)])
            x_list.append(time)
            y_list.append(y_val)
    
    plt.bar(x_list, y_list)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.savefig(output_file)
    plt.clf()

if __name__ == "__main__":
    extra = ""
    plotter("./build/background_stats.csv", "time", "memoryUsage", "/users/nithinv/graphs/memory" + extra + ".png", "time", "Memory usage (MB)")
    plotter("./build/background_stats.csv", "time", "compactionScheduledCount", "/users/nithinv/graphs/compaction" + extra + ".png", "time", "Number of compactions scheduled")
    plotter("./build/background_stats.csv", "time", "levelWiseData::writes", "/users/nithinv/graphs/compaction_writes" + extra + ".png", "time", "Compaction writes (MB)")
    plotter("./build/background_stats.csv", "time", "levelWiseData::reads", "/users/nithinv/graphs/compaction_reads" + extra + ".png", "time", "Compaction reads (MB)")
    plotter("./build/background_stats.csv", "time", "levelWiseData::files", "/users/nithinv/graphs/files_created" + extra + ".png", "time", "Number of files created in the interval")
    plotter("./build/background_stats.csv", "time", "levelWiseData::time", "/users/nithinv/graphs/compaction_time" + extra + ".png", "time", "Compaction time (s)")
    plotter("./build/background_stats.csv", "time", "writeBufferSize", "/users/nithinv/graphs/write_buffer_size" + extra + ".png", "time", "Write buffer size (MB)")
    plotter("./build/foreground_stats.csv", "time", "writes", "/users/nithinv/graphs/writes" + extra + ".png", "time", "Number of writes in the interval")
    plotter("./build/foreground_stats.csv", "time", "throughput", "/users/nithinv/graphs/throughput" + extra + ".png", "time", "Throughput in the interval (MB/s)")