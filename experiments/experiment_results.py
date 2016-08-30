import csv
import logging
import sys
import traceback
from cProfile import Profile
from os import path, listdir
from typing import List, Any, Dict

from experiments.experiment_run import ExperimentsRun
from shared.connection.base_connection import BaseConnection
from shared.utils.measure_util import connections_to_csv, pstats_to_step_timings, algorithm_steps

OUTPUT_DIRECTORY = 'data/experiments/results'


class ExperimentResults(object):
    """
    Utility class for exporting experiment results.
    """

    @staticmethod
    def experiment_results_directory(experiments_run: ExperimentsRun) -> str:
        """
        Gets the base directory for the results of the experiment
        :param experiments_run: The current experiment run
        """
        return path.join(OUTPUT_DIRECTORY,
                         experiments_run.experiment.get_name(),
                         experiments_run.device_name,
                         experiments_run.timestamp)

    @staticmethod
    def experiment_case_iteration_results_directory(experiments_run: ExperimentsRun) -> str:
        """
        Gets the base directory for the results of the experiment for the current case and implementation.
        :require: experiments_run.current_implementation is not None and experiments_run.current_case is not None
        :param experiments_run: The current experiment run.
        """
        return path.join(ExperimentResults.experiment_results_directory(experiments_run),
                         experiments_run.current_implementation.get_name(),
                         experiments_run.current_case.name,
                         str(experiments_run.iteration))

    @staticmethod
    def output_cpu_usage(experiments_run: ExperimentsRun, cpu_usage: float) -> None:
        """
        Output the cpu usage of the previous experiment.
        :param experiments_run: The current experiments run
        :param cpu_usage: The measured cpu usage
        """
        directory = ExperimentResults.experiment_case_iteration_results_directory(experiments_run)
        with open(path.join(directory, 'cpu.txt'), 'w') as file:
            file.write(str(cpu_usage))

    @staticmethod
    def output_error(experiments_run: ExperimentsRun) -> None:
        """
        Output an error. The last exception is printed.
        :param experiments_run: The current experiments run
        """
        directory = ExperimentResults.experiment_case_iteration_results_directory(experiments_run)
        logging.error(traceback.format_exc())
        traceback.print_exc(file=sys.stderr)
        with open(path.join(directory, 'ERROR.txt'), 'w') as file:
            traceback.print_exc(file=file)

    @staticmethod
    def output_connections(experiments_run: ExperimentsRun, connections: List[BaseConnection]) -> None:
        """
        Output the network usage.
        :param experiments_run: The current experiments run.
        :param connections: The connections to output the usage of.
        """
        directory = ExperimentResults.experiment_case_iteration_results_directory(experiments_run)
        connections_to_csv(connections, path.join(directory, 'network.csv'))

        output_file_path = path.join(ExperimentResults.experiment_results_directory(experiments_run), 'network.csv')

        rows = []
        for connection in connections:
            for (name, sizes) in connection.benchmarks.items():
                for size in sizes:
                    rows.append((
                        experiments_run.current_implementation.get_name(),
                        experiments_run.current_case.name,
                        experiments_run.iteration,
                        connection.__class__.__name__,
                        name,
                        size
                    ))

        ExperimentResults.append_rows_to_file(
            output_file_path,
            ('implementation', 'case', 'iteration', 'connection', 'name', 'size'),
            rows
        )

    @staticmethod
    def output_memory_usages(experiments_run: ExperimentsRun, memory_usages: List[Any]) -> None:
        """
        Output the memory usages.
        :param experiments_run: The current experiments run.
        :param memory_usages: The list of memory usages.
        :return:
        """
        directory = ExperimentResults.experiment_case_iteration_results_directory(experiments_run)
        with open(path.join(directory, 'memory.csv'), 'w') as file:
            writer = csv.DictWriter(file, fieldnames=[
                'rss', 'vms', 'shared', 'text', 'lib', 'data', 'dirty', 'uss', 'pss', 'swap'
            ])
            writer.writeheader()
            for row in memory_usages:
                writer.writerow(row._asdict())

    @staticmethod
    def output_storage_space(experiments_run: ExperimentsRun) -> None:
        """
        Output the storage space used by the different parties.
        :param experiments_run: The current experiments run.
        """
        # directory = ExperimentResults.experiment_case_iteration_results_directory(experiments_run)
        insurance_storage = experiments_run.experiment.get_insurance_storage_path()
        client_storage = experiments_run.experiment.get_user_client_storage_path()
        authority_storage = experiments_run.experiment.get_attribute_authority_storage_path()

        output_file_path = path.join(ExperimentResults.experiment_results_directory(experiments_run), 'storage.csv')
        headers = ('implementation', 'case', 'iteration', 'entity', 'filename', 'size')
        rows = list()

        for file in listdir(insurance_storage):
            size = path.getsize(path.join(insurance_storage, file))
            rows.append((
                experiments_run.current_implementation.get_name(),
                experiments_run.current_case.name,
                experiments_run.iteration,
                'insurance',
                file,
                size
            ))

        for file in listdir(client_storage):
            size = path.getsize(path.join(client_storage, file))
            rows.append((
                experiments_run.current_implementation.get_name(),
                experiments_run.current_case.name,
                experiments_run.iteration,
                'client',
                file,
                size
            ))

        for file in listdir(authority_storage):
            size = path.getsize(path.join(authority_storage, file))
            rows.append((
                experiments_run.current_implementation.get_name(),
                experiments_run.current_case.name,
                experiments_run.iteration,
                'authority',
                file,
                size
            ))

        # with open(path.join(directory, 'storage.csv'), 'w') as output:
        #     writer = csv.writer(output)
        #     writer.writerow(headers)
        #     for row in rows:
        #         writer.writerow(row)

        ExperimentResults.append_rows_to_file(
            output_file_path,
            headers,
            rows
        )

    @staticmethod
    def output_timings(experiments_run: ExperimentsRun, profile: Profile) -> None:
        """
        Output the timings measured by the profiler.
        :param experiments_run: The current experiments run.
        :param profile: The profile.
        """
        directory = ExperimentResults.experiment_case_iteration_results_directory(experiments_run)

        # Write raw measurements
        stats_file_path = path.join(directory, 'timings.pstats')
        profile.dump_stats(stats_file_path)

        # Write formatted measurements
        # pstats_to_csv(stats_file_path,
        #              path.join(directory, 'timings.csv'))
        # pstats_to_csv_filtered(stats_file_path,
        #                       path.join(directory, 'timings2.csv'))

        # Convert to step names and append to file
        step_timings = pstats_to_step_timings(stats_file_path, path.join(directory, 'step_timings.csv'))

        output_file_path = path.join(ExperimentResults.experiment_results_directory(experiments_run), 'timings.csv')
        headers = ['implementation', 'case', 'iteration'] + list(algorithm_steps)
        row = {
            'implementation': experiments_run.current_implementation.get_name(),
            'case': experiments_run.current_case.name,
            'iteration': experiments_run.iteration
        }
        row.update(step_timings)

        ExperimentResults.append_dict_to_file(
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
    def append_dict_to_file(file_path, headers, row: Dict[str, Any]):
        write_header = not path.exists(file_path)
        with open(file_path, 'a') as file:
            writer = csv.DictWriter(file, headers)
            if write_header:
                writer.writeheader()
            writer.writerow(row)
