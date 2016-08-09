import json
from pprint import pprint


class BaseConnection(object):
    def __init__(self, benchmark: bool = False) -> None:
        self.benchmark = benchmark
        self.benchmarks = dict()  # type: Dict[str, List[int]]

    def dumps(self):
        pprint(self.benchmarks)

    def dump(self, file_pointer):
        json.dump(self.benchmark, file_pointer)

    def add_benchmark(self, name: str, size: int) -> None:
        if name not in self.benchmarks:
            self.benchmarks[name] = list()
        self.benchmarks[name].append(size)
