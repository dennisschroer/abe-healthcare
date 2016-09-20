import json
from typing import Dict
from typing import List


class BaseConnection(object):
    def __init__(self, benchmark: bool = False) -> None:
        self.benchmark = benchmark
        self.benchmarks = dict()  # type: Dict[str, List[int]]

    def dumps(self):
        return json.dumps(self.benchmarks)

    def dump(self, file_pointer):
        json.dump(self.benchmarks, file_pointer)

    def add_benchmark(self, name: str, size: int) -> None:
        if name not in self.benchmarks:
            self.benchmarks[name] = list()
        self.benchmarks[name].append(size)
