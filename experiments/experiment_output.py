import csv
import logging
import sys
import traceback
from cProfile import Profile
from os import path, listdir
from typing import List, Any, Dict

from experiments.experiments_sequence import ExperimentsSequence
from shared.connection.base_connection import BaseConnection
from shared.utils.measure_util import connections_to_csv, pstats_to_step_timings, algorithm_steps

OUTPUT_DIRECTORY = 'data/experiments/results'

output_detailed = False


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
    def output_cpu_usage(experiments_run: ExperimentsSequence, cpu_usage: float) -> None:
        """
        Output the cpu usage of the previous experiment.
        :param experiments_run: The current experiments run
        :param cpu_usage: The measured cpu usage
        """
        if output_detailed:
            directory = ExperimentOutput.experiment_case_iteration_results_directory(experiments_run)
            with open(path.join(directory, 'cpu.txt'), 'w') as file:
                file.write(str(cpu_usage))

        output_file_path = path.join(ExperimentOutput.experiment_results_directory(experiments_run), 'cpu.csv')
        headers = ('implementation', 'case', 'iteration', 'usage')
        ExperimentOutput.append_row_to_file(
            output_file_path,
            headers,
            (
                experiments_run.state.current_implementation.get_name(),
                experiments_run.state.current_case.name,
                experiments_run.state.iteration,
                cpu_usage
            )
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
    def output_connections(experiments_run: ExperimentsSequence, connections: List[BaseConnection]) -> None:
        """
        Output the network usage.
        :param experiments_run: The current experiments run.
        :param connections: The connections to output the usage of.
        """
        if output_detailed:
            directory = ExperimentOutput.experiment_case_iteration_results_directory(experiments_run)
            connections_to_csv(connections, path.join(directory, 'network.csv'))

        output_file_path = path.join(ExperimentOutput.experiment_results_directory(experiments_run), 'network.csv')

        rows = []
        for connection in connections:
            for (name, sizes) in connection.benchmarks.items():
                for size in sizes:
                    rows.append((
                        experiments_run.state.current_implementation.get_name(),
                        experiments_run.state.current_case.name,
                        experiments_run.state.iteration,
                        connection.__class__.__name__,
                        name,
                        size
                    ))

        ExperimentOutput.append_rows_to_file(
            output_file_path,
            ('implementation', 'case', 'iteration', 'connection', 'name', 'size'),
            rows
        )

    @staticmethod
    def output_memory_usages(experiments_run: ExperimentsSequence, memory_usages: List[Any]) -> None:
        """
        Output the memory usages.
        :param experiments_run: The current experiments run.
        :param memory_usages: The list of memory usages.
        :return:
        """
        if output_detailed:
            directory = ExperimentOutput.experiment_case_iteration_results_directory(experiments_run)
            with open(path.join(directory, 'memory.csv'), 'w') as file:
                writer = csv.DictWriter(file, fieldnames=[
                    'rss', 'vms', 'shared', 'text', 'lib', 'data', 'dirty', 'uss', 'pss', 'swap'
                ])
                writer.writeheader()
                for row in memory_usages:
                    writer.writerow(row._asdict())

    @staticmethod
    def output_storage_space(experiments_run: ExperimentsSequence) -> None:
        """
        Output the storage space used by the different parties.
        :param experiments_run: The current experiments run.
        """
        # directory = ExperimentOutput.experiment_case_iteration_results_directory(experiments_run)
        insurance_storage = experiments_run.experiment.get_insurance_storage_path()
        client_storage = experiments_run.experiment.get_user_client_storage_path()
        authority_storage = experiments_run.experiment.get_attribute_authority_storage_path()
        central_authority_storage = experiments_run.experiment.get_central_authority_storage_path()

        output_file_path = path.join(ExperimentOutput.experiment_results_directory(experiments_run), 'storage.csv')
        headers = ('implementation', 'case', 'iteration', 'entity', 'filename', 'size')
        rows = list()

        for file in listdir(insurance_storage):
            size = path.getsize(path.join(insurance_storage, file))
            rows.append((
                experiments_run.state.current_implementation.get_name(),
                experiments_run.state.current_case.name,
                experiments_run.state.iteration,
                'insurance',
                file,
                size
            ))

        for file in listdir(client_storage):
            size = path.getsize(path.join(client_storage, file))
            rows.append((
                experiments_run.state.current_implementation.get_name(),
                experiments_run.state.current_case.name,
                experiments_run.state.iteration,
                'client',
                file,
                size
            ))

        for file in listdir(authority_storage):
            size = path.getsize(path.join(authority_storage, file))
            rows.append((
                experiments_run.state.current_implementation.get_name(),
                experiments_run.state.current_case.name,
                experiments_run.state.iteration,
                'authority',
                file,
                size
            ))

        for file in listdir(central_authority_storage):
            size = path.getsize(path.join(central_authority_storage, file))
            rows.append((
                experiments_run.state.current_implementation.get_name(),
                experiments_run.state.current_case.name,
                experiments_run.state.iteration,
                'central_authority',
                file,
                size
            ))

        if output_detailed:
            directory = ExperimentOutput.experiment_case_iteration_results_directory(experiments_run)
            with open(path.join(directory, 'storage.csv'), 'w') as output:
                writer = csv.writer(output)
                writer.writerow(headers)
                for row in rows:
                    writer.writerow(row)

        ExperimentOutput.append_rows_to_file(
            output_file_path,
            headers,
            rows
        )

    @staticmethod
    def output_timings(experiments_run: ExperimentsSequence, profile: Profile) -> None:
        """
        Output the timings measured by the profiler.
        :param experiments_run: The current experiments run.
        :param profile: The profile.
        """
        directory = ExperimentOutput.experiment_case_iteration_results_directory(experiments_run)
        stats_file_path = path.join(directory, 'timings.pstats')

        # Write raw stats
        profile.dump_stats(stats_file_path)

        # Process raw stats
        step_timings = pstats_to_step_timings(stats_file_path)

        # Output processed stats
        output_file_path = path.join(ExperimentOutput.experiment_results_directory(experiments_run), 'timings.csv')
        headers = ['implementation', 'case', 'iteration'] + list(algorithm_steps)
        row = {
            'implementation': experiments_run.state.current_implementation.get_name(),
            'case': experiments_run.state.current_case.name,
            'iteration': experiments_run.state.iteration
        }
        row.update(step_timings)

        ExperimentOutput.append_dict_to_file(
            output_file_path,
            headers,
            row
        )

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
