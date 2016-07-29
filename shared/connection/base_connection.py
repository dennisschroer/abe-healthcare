from pprint import pprint


class BaseConnection(object):
    def __init__(self, benchmark: bool = False) -> None:
        self.benchmark = benchmark
        self.benchmarks = dict()  # type: Dict[str, List[int]]

    def dump_benchmarks(self):
        pprint(self.benchmarks)

    def add_benchmark(self, name: str, size: int) -> None:
        if name not in self.benchmarks:
            self.benchmarks[name] = list()
        self.benchmarks[name].append(size)
