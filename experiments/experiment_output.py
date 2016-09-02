import csv
import logging
import sys
import traceback
from cProfile import Profile
from os import path, listdir
from typing import List, Any, Dict
from typing import Union

from experiments.experiments_sequence import ExperimentsSequence
from shared.connection.base_connection import BaseConnection
from shared.utils.measure_util import connections_to_csv, pstats_to_step_timings

OUTPUT_DIRECTORY = 'data/experiments/results'

OUTPUT_DETAILED = False


class ExperimentOutput(object):
    """
    Utility class for exporting experiment results.
    """

    @staticmethod
    def experiment_results_directory(experiments_run: ExperimentsSequence) -> str:
        """
        Gets the base directory for the results of the experiment
        :param experiments_run: The current experiment run
        """
        return path.join(OUTPUT_DIRECTORY,
                         experiments_run.experiment.get_name(),
                         experiments_run.device_name,
                         experiments_run.timestamp)

    @staticmethod
    def experiment_case_iteration_results_directory(experiments_run: ExperimentsSequence) -> str:
        """
        Gets the base directory for the results of the experiment for the current case and implementation.
        :require: experiments_run.current_implementation is not None and experiments_run.current_case is not None
        :param experiments_run: The current experiment run.
        """
        return path.join(ExperimentOutput.experiment_results_directory(experiments_run),
                         experiments_run.state.current_implementation.get_name(),
                         experiments_run.state.current_case.name,
                         str(experiments_run.state.iteration))

    @staticmethod
    def output_cpu_usage(experiments_sequence: ExperimentsSequence, cpu_usage: float) -> None:
        """
        Output the cpu usage of the previous experiment.
        :param experiments_sequence: The current experiments run
        :param cpu_usage: The measured cpu usage
        """
        if OUTPUT_DETAILED:
            directory = ExperimentOutput.experiment_case_iteration_results_directory(experiments_sequence)
            with open(path.join(directory, 'cpu.txt'), 'w') as file:
                file.write(str(cpu_usage))

        output_file_path = path.join(ExperimentOutput.experiment_results_directory(experiments_sequence), 'cpu.csv')
        headers = ['case'] + list(map(lambda i: i.__class__.__name__, experiments_sequence.implementations))
        implementation_index = ExperimentOutput.determine_implementation_index(experiments_sequence)

        ExperimentOutput.append_row_to_file(
            output_file_path,
            headers,
            ExperimentOutput.create_row(experiments_sequence.state.current_case.name, cpu_usage, implementation_index)
        )

    @staticmethod
    def output_error(experiments_run: ExperimentsSequence) -> None:
        """
        Output an error. The last exception is printed.
        :param experiments_run: The current experiments run
        """
        directory = ExperimentOutput.experiment_case_iteration_results_directory(experiments_run)
        logging.error(traceback.format_exc())
        traceback.print_exc(file=sys.stderr)
        with open(path.join(directory, 'ERROR.txt'), 'w') as file:
            traceback.print_exc(file=file)

    @staticmethod
    def output_connections(experiments_sequence: ExperimentsSequence, connections: List[BaseConnection]) -> None:
        """
        Output the network usage.
        :param experiments_run: The current experiments run.
        :param connections: The connections to output the usage of.
        """
        if OUTPUT_DETAILED:
            directory = ExperimentOutput.experiment_case_iteration_results_directory(experiments_sequence)
            connections_to_csv(connections, path.join(directory, 'network.csv'))

        values = dict()
        for connection in connections:
            for (name, sizes) in connection.benchmarks.items():
                for size in sizes:
                    values[name] = size

        ExperimentOutput.output_case_results(experiments_sequence, 'network', values)

    @staticmethod
    def output_memory_usages(experiments_run: ExperimentsSequence, memory_usages: List[Any]) -> None:
        """
        Output the memory usages.
        :param experiments_run: The current experiments run.
        :param memory_usages: The list of memory usages.
        :return:
        """
        if OUTPUT_DETAILED:
            directory = ExperimentOutput.experiment_case_iteration_results_directory(experiments_run)
            with open(path.join(directory, 'memory.csv'), 'w') as file:
                writer = csv.DictWriter(file, fieldnames=[
                    'rss', 'vms', 'shared', 'text', 'lib', 'data', 'dirty', 'uss', 'pss', 'swap'
                ])
                writer.writeheader()
                for row in memory_usages:
                    writer.writerow(row._asdict())

    @staticmethod
    def output_storage_space(experiments_sequence: ExperimentsSequence) -> None:
        """
        Output the storage space used by the different parties.
        :param experiments_sequence: The current experiments run.
        """
        insurance_storage = experiments_sequence.experiment.get_insurance_storage_path()
        client_storage = experiments_sequence.experiment.get_user_client_storage_path()
        authority_storage = experiments_sequence.experiment.get_attribute_authority_storage_path()
        central_authority_storage = experiments_sequence.experiment.get_central_authority_storage_path()

        values = dict()

        for file in listdir(insurance_storage):
            size = path.getsize(path.join(insurance_storage, file))
            values[path.splitext(file)[1]] = size

        for file in listdir(client_storage):
            size = path.getsize(path.join(client_storage, file))
            values[file] = size

        for file in listdir(authority_storage):
            size = path.getsize(path.join(authority_storage, file))
            values[file] = size

        for file in listdir(central_authority_storage):
            size = path.getsize(path.join(central_authority_storage, file))
            values[file] = size

        ExperimentOutput.output_case_results(experiments_sequence, 'storage', values)

    @staticmethod
    def output_timings(experiments_sequence: ExperimentsSequence, profile: Profile) -> None:
        """
        Output the timings measured by the profiler.
        :param experiments_sequence: The current experiments run.
        :param profile: The profile.
        """
        directory = ExperimentOutput.experiment_results_directory(experiments_sequence)
        stats_file_path = path.join(directory, 'timings.pstats')

        # Write raw stats
        profile.dump_stats(stats_file_path)

        # Process raw stats
        step_timings = pstats_to_step_timings(stats_file_path)
        step_timings['total'] = sum(step_timings.values())

        ExperimentOutput.output_case_results(experiments_sequence, 'timings', step_timings)

    @staticmethod
    def output_case_results(experiments_sequence: ExperimentsSequence, name: str, values: Dict[str, Any]):
        headers = ['case/step'] + list(map(lambda i: i.__class__.__name__, experiments_sequence.implementations))
        implementation_index = ExperimentOutput.determine_implementation_index(experiments_sequence)

        case_output_file_path = path.join(ExperimentOutput.experiment_results_directory(experiments_sequence),
                                          '%s-case-%s.csv' % (name, experiments_sequence.state.current_case.name))

        case_rows = list()
        for category, value in values.items():
            case_rows.append(ExperimentOutput.create_row(category, value, implementation_index))
            category_row = ExperimentOutput.create_row(experiments_sequence.state.current_case.name, value,
                                                       implementation_index)

            category_output_file_path = path.join(ExperimentOutput.experiment_results_directory(experiments_sequence),
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

    @staticmethod
    def determine_implementation_index(experiments_sequence: ExperimentsSequence):
        return experiments_sequence.implementations.index(experiments_sequence.state.current_implementation)

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
