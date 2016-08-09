import csv
import marshal
from typing import Dict, List

from shared.connection.base_connection import BaseConnection


def pstats_to_csv(input_file_path, output_file_path):
    with open(input_file_path, 'rb') as input_file:
        with open(output_file_path, 'w') as output_file:
            stats = marshal.load(input_file)  # type: Dict
            # The output dictionary maps a tuple describing a function (filename, line number, name)
            # to a tuple of statistics.
            # The tuple's data is (number of calls, number of non-recursive calls, total time,
            # cumulative time, subcall statistics).
            headers = ['filename', 'line number', 'name', 'number of calls', 'number or non-recursive calls', 'total time', 'cumtime']
            writer = csv.writer(output_file)
            writer.writerow(headers)
            for (function, statistics) in stats.items():
                writer.writerow(list(function)[0:3] + list(statistics)[0:4])


def connections_to_csv(connections: List[BaseConnection], output_file_path):
    with open(output_file_path, 'w') as output_file:
        headers = ['connection', 'name', 'size']
        writer = csv.writer(output_file)
        writer.writerow(headers)
        for connection in connections:
            for (name, sizes) in connection.benchmarks.items():
                for size in sizes:
                    writer.writerow((connection.__class__.__name__, name, size))
