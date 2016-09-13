import csv
import logging
import sys
import traceback
from cProfile import Profile
from os import path, listdir
from typing import List, Any, Dict
from typing import Union

from experiments.enum.implementations import implementations
from experiments.experiment_state import ExperimentState
from experiments.experiments_sequence_state import ExperimentsSequenceState
from shared.connection.base_connection import BaseConnection
from shared.utils.measure_util import connections_to_csv, pstats_to_step_timings

OUTPUT_DIRECTORY = 'data/experiments/results'

OUTPUT_DETAILED = False


class ExperimentOutput(object):
    """
    Utility class for exporting experiment results.
    """

    def __init__(self, experiment_name: str, state: ExperimentState, sequence_state: ExperimentsSequenceState) -> None:
        self.experiment_name = experiment_name
        self.state = state
        self.sequence_state = sequence_state

    def experiment_results_directory(self) -> str:
        """
        Gets the base directory for the results of the experiment
        """
        return path.join(OUTPUT_DIRECTORY,
                         self.experiment_name,
                         self.sequence_state.device_name,
                         self.sequence_state.timestamp
                         )

    def experiment_case_iteration_results_directory(self) -> str:
        """
        Gets the base directory for the results of the experiment for the current case and implementation.
        :require: experiments_run.implementation is not None and experiments_run.case is not None
        """
        return path.join(
            self.experiment_results_directory(),
            self.sequence_state.implementation.get_name(),
            self.state.case.name
        )

    def output_cpu_usage(self, cpu_usage: float) -> None:
        """
        Output the cpu usage of the previous experiment.
        :param cpu_usage: The measured cpu usage
        """
        # if OUTPUT_DETAILED:
        #     directory = ExperimentOutput.experiment_case_iteration_results_directory(experiments_state)
        #     with open(path.join(directory, 'cpu.txt'), 'w') as file:
        #         file.write(str(cpu_usage))

        output_file_path = path.join(self.experiment_results_directory(), 'cpu.csv')
        headers = ['case'] + list(map(lambda i: i.get_name(), implementations))  # type: ignore
        implementation_index = self.determine_implementation_index()

        ExperimentOutput.append_row_to_file(
            output_file_path,
            headers,
            ExperimentOutput.create_row(self.state.case.name, cpu_usage, implementation_index)
        )

    @staticmethod
    def output_error() -> None:
        """
        Output an error. The last exception is printed.
        """
        logging.error(traceback.format_exc())
        traceback.print_exc(file=sys.stderr)

    def output_connections(self, connections: List[BaseConnection]) -> None:
        """
        Output the network usage.
        :param connections: The connections to output the usage of.
        """
        if OUTPUT_DETAILED:
            directory = self.experiment_case_iteration_results_directory()
            connections_to_csv(connections, path.join(directory, 'network.csv'))

        values = dict()
        for connection in connections:
            for (name, sizes) in connection.benchmarks.items():
                for size in sizes:
                    values[name] = size

        self.output_case_results('network', values)

    def output_memory_usages(self, memory_usages: List[Any]) -> None:
        """
        Output the memory usages.
        :param memory_usages: The list of memory usages.
        :return:
        """
        values = dict()
        i = 0
        for row in memory_usages:
            values[str(i)] = row.rss + row.swap
            i += 1

        self.output_case_results('memory', values, skip_categories=True)

        if OUTPUT_DETAILED:
            directory = self.experiment_results_directory()
            with open(path.join(directory, 'memory.csv'), 'w') as file:
                writer = csv.DictWriter(file, fieldnames=[
                    'rss', 'vms', 'shared', 'text', 'lib', 'data', 'dirty', 'uss', 'pss', 'swap'
                ])
                writer.writeheader()
                for row in memory_usages:
                    writer.writerow(row._asdict())

    def output_storage_space(self, directories: List[dict]) -> None:
        """
        Output the storage space used by the different parties.
        :param directories: A list of directory options. Each directory option contains at least a 'path' value.
        An 'filename_mapper' value is optional.
        """
        # insurance_storage = experiment.get_insurance_storage_path()
        # client_storage = experiment.get_user_client_storage_path()
        # authority_storage = experiment.get_attribute_authority_storage_path()
        # central_authority_storage = experiment.get_central_authority_storage_path()

        values = dict()

        for directory_options in directories:
            directory_path = directory_options['path']
            filename_mapper = directory_options['filename_mapper'] if 'filename_mapper' in directory_options else lambda \
                x: x

            for file in listdir(directory_path):
                size = path.getsize(path.join(directory_path, file))
                values[filename_mapper(file)] = size

        # for file in listdir(insurance_storage):
        #     size = path.getsize(path.join(insurance_storage, file))
        #     values[path.splitext(file)[1]] = size
        #
        # for file in listdir(client_storage):
        #     size = path.getsize(path.join(client_storage, file))
        #     values[file] = size
        #
        # for file in listdir(authority_storage):
        #     size = path.getsize(path.join(authority_storage, file))
        #     values[file] = size
        #
        # for file in listdir(central_authority_storage):
        #     size = path.getsize(path.join(central_authority_storage, file))
        #     values[file] = size

        self.output_case_results('storage', values)

    def output_timings(self, profile: Profile) -> None:
        """
        Output the timings measured by the profiler.
        :param profile: The profile.
        """
        directory = self.experiment_results_directory()
        stats_file_path = path.join(directory, 'timings.pstats')

        # Write raw stats
        profile.dump_stats(stats_file_path)

        # Process raw stats
        step_timings = pstats_to_step_timings(stats_file_path)
        step_timings['total'] = sum(step_timings.values())

        self.output_case_results('timings', step_timings, skip_categories_in_case_files=['total'])

    def output_case_results(self, name: str, values: Dict[str, Any],
                            skip_categories=False, skip_categories_in_case_files: List[str] = list()) -> None:
        """
        Output the results of a single case to the different files (one file for the current case, one file
        for each category)
        :param name: The name of the measurement (for example 'network' or 'memory')
        :param values: A dictionary of category to value. A category is for example a step in the algorithm ('encrypt', 'decrypt'),
        or filename for storage.
        :param skip_categories: If true, skip appending to the category specific files
        :param skip_categories_in_case_files: Categories in this list will not be added to the case file. This can for
        example be used to create a file containing totals, without having a total category in the case file.
        """
        headers = ['case/step'] + list(map(lambda i: i.get_name(), implementations))  # type: ignore
        implementation_index = self.determine_implementation_index()

        case_output_file_path = path.join(self.experiment_results_directory(),
                                          '%s-case-%s.csv' % (name, self.state.case.name))

        case_rows = list()
        for category, value in values.items():
            if category not in skip_categories_in_case_files:
                case_rows.append(ExperimentOutput.create_row(category, value, implementation_index))

            if not skip_categories:
                category_row = ExperimentOutput.create_row(self.state.case.name, value,
                                                           implementation_index)
                category_output_file_path = path.join(
                    self.experiment_results_directory(),
                    '%s-category-%s.csv' % (name, category))
                ExperimentOutput.append_row_to_file(
                    category_output_file_path,
                    headers,
                    category_row
                )

        ExperimentOutput.append_rows_to_file(
            case_output_file_path,
            headers,
            case_rows
        )

    @staticmethod
    def create_row(category: str, value: float, implementation_index):
        row = [None] * 5  # type: List[Union[str, Any]]
        row[0] = category
        row[implementation_index + 1] = value
        return row

    def determine_implementation_index(self):
        return implementations.index(self.sequence_state.implementation)

    @staticmethod
    def append_rows_to_file(file_path, headers, rows):
        write_header = not path.exists(file_path)
        with open(file_path, 'a') as file:
            writer = csv.writer(file)
            if write_header:
                writer.writerow(headers)
            for row in rows:
                writer.writerow(row)

    @staticmethod
    def append_row_to_file(file_path, headers, row):
        write_header = not path.exists(file_path)
        with open(file_path, 'a') as file:
            writer = csv.writer(file)
            if write_header:
                writer.writerow(headers)
            writer.writerow(row)

    @staticmethod
    def append_dict_to_file(file_path, headers, row: Dict[str, Any]):
        write_header = not path.exists(file_path)
        with open(file_path, 'a') as file:
            writer = csv.DictWriter(file, headers)
            if write_header:
                writer.writeheader()
            writer.writerow(row)
