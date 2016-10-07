import json
import logging
from typing import Dict
from typing import List


class BaseConnection(object):
    def __init__(self, benchmark: bool = False, identifier: str = None) -> None:
        self.benchmark = benchmark
        self.identifier = identifier
        self.benchmarks = dict()  # type: Dict[str, List[int]]

    def dumps(self):
        return json.dumps(self.benchmarks)

    def dump(self, file_pointer):
        json.dump(self.benchmarks, file_pointer)

    def add_benchmark(self, name: str, size: int) -> None:
        benchmark_name = "%s.%s" % (self.identifier, name)
        if benchmark_name not in self.benchmarks:
            self.benchmarks[benchmark_name] = list()
        else:
            print("Connection benchmark %s already exists" % benchmark_name)
            logging.waring("Connection benchmark %s already exists" % benchmark_name)
        self.benchmarks[benchmark_name].append(size)
