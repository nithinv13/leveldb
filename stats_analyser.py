import csv
import matplotlib.pyplot as plt

def plotter(file_name, x, y, output_file):
    with open(file_name) as f:
        csv_reader = csv.reader(f, delimiter=',')
        csv_reader = list(csv_reader)
        header = csv_reader[0]
        start_time = float(csv_reader[1][0])
        time_list = []
        memory_usage_list = []
        for row in csv_reader[1:]:
            time = (float(row[header.index(x)]) - start_time) / 10**6
            memory_usage = float(row[header.index(y)])
            time_list.append(time)
            memory_usage_list.append(memory_usage)
    
    plt.bar(time_list, memory_usage_list)
    plt.savefig(output_file)
    plt.clf()

if __name__ == "__main__":
    plotter("./build/background_stats.csv", "time", "memoryUsage", "/users/nithinv/graphs/memory.png")
    plotter("./build/background_stats.csv", "time", "compactionScheduledCount", "/users/nithinv/graphs/compaction.png")
    plotter("./build/foreground_stats.csv", "time", "writes", "/users/nithinv/graphs/writes.png")
    plotter("./build/foreground_stats.csv", "time", "throughput", "/users/nithinv/graphs/throughput.png")