class BaseConnection(object):
    def __init__(self, benchmark=False):
        self.benchmark = benchmark
        self.benchmarks = dict()

    def dump_benchmarks(self):
        print(self.benchmarks)

    def add_benchmark(self, name, size):
        if name not in self.benchmarks:
            self.benchmarks[name] = list()
        self.benchmarks[name].append(size)