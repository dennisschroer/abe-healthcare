import csv
import logging
import traceback
from cProfile import Profile
from multiprocessing import Condition  # type: ignore
from multiprocessing import Process
from multiprocessing import Value
from os import makedirs, listdir
from os import path
from time import sleep
from typing import List, Any

import psutil

from experiments.base_experiment import BaseExperiment, ExperimentCase
from experiments.experiment_run import ExperimentsRun
from experiments.file_size_experiment import FileSizeExperiment
from experiments.policy_size_experiment import PolicySizeExperiment
from shared.connection.base_connection import BaseConnection
from shared.implementations.base_implementation import BaseImplementation
from shared.implementations.dacmacs13_implementation import DACMACS13Implementation
from shared.implementations.rd13_implementation import RD13Implementation
from shared.implementations.rw15_implementation import RW15Implementation
from shared.implementations.taac12_implementation import TAAC12Implementation
from shared.utils.measure_util import pstats_to_csv, connections_to_csv, pstats_to_csv2, pstats_to_step_timings

debug = False

OUTPUT_DIRECTORY = 'data/experiments/results'


class ExperimentsRunner(object):
    """
    Runner responsible for running the experiments and outputting the measurements.
    """

    def __init__(self) -> None:
        if not path.exists(OUTPUT_DIRECTORY):
            makedirs(OUTPUT_DIRECTORY)
        self.implementations = [
            DACMACS13Implementation(),
            RD13Implementation(),
            RW15Implementation(),
            TAAC12Implementation()
        ]
        self._timestamp = None  # type: str
        self._device_name = None  # type: str
        self.current_run = None  # type: ExperimentsRun

    def run_base_experiments(self) -> None:
        self.run_experiments_run(ExperimentsRun(BaseExperiment(), 1))

    def run_file_size_experiments(self) -> None:
        self.run_experiments_run(ExperimentsRun(FileSizeExperiment(), 1))

    def run_policy_size_experiments(self) -> None:
        self.run_experiments_run(ExperimentsRun(PolicySizeExperiment(), 1))

    def run_experiments_run(self, experiments_run: ExperimentsRun) -> None:
        self.current_run = experiments_run

        # Create directories
        if not path.exists(ExperimentsRunner.experiment_results_directory(self.current_run)):
            makedirs(ExperimentsRunner.experiment_results_directory(self.current_run))

        # Setup logging
        self.setup_logging()

        logging.info("Device '%s' starting experiment '%s' with timestamp '%s', running %d times" % (
            experiments_run.device_name, experiments_run.experiment.get_name(), experiments_run.timestamp,
            experiments_run.amount))

        experiments_run.experiment.global_setup()

        logging.info("Global setup finished")

        for i in range(0, experiments_run.amount):
            experiments_run.experiment.run_counter = i + 1
            self.run_current_experiment()

    def run_current_experiment(self):
        for implementation in self.implementations:
            self.run_current_experiment_for_implementation(implementation)

    def run_current_experiment_for_implementation(self, implementation: BaseImplementation) -> None:
        for case in self.current_run.experiment.cases:
            self.run_current_experiment_case(implementation, case)

    def run_current_experiment_case(self, implementation: BaseImplementation, case: ExperimentCase) -> None:
        logging.info("=> Run %d/%d of %s, implementation=%s (%d/%d), case=%s (%d/%d)" % (
            self.current_run.experiment.run_counter,
            self.current_run.amount,
            self.current_run.experiment.get_name(),
            implementation.get_name(),
            self.implementations.index(implementation) + 1,
            len(self.implementations),
            case.name,
            self.current_run.experiment.cases.index(case) + 1,
            len(self.current_run.experiment.cases)
        ))

        # Create a lock
        lock = Condition()
        lock.acquire()

        # Create output directory
        output_directory = self.experiment_case_results_directory(self.current_run, implementation, case)
        if not path.exists(output_directory):
            makedirs(output_directory)

        # Create a separate process
        is_running = Value('b', False)
        p = Process(target=self.run_experiment_case_synchronously,
                    args=(self.current_run, implementation, case, lock, is_running))

        logging.debug("debug 1 -> start process")

        # Start the process
        p.start()

        # Wait until the setup of the experiment is finished
        lock.wait()

        logging.debug("debug 4 -> start monitoring")

        # Setup is finished, start monitoring
        process = psutil.Process(p.pid)  # type: ignore
        memory_usages = list()
        process.cpu_percent()

        # Release the lock, signaling the experiment to start, and wait for the experiment to finish
        lock.notify()
        is_running.value = True  # type: ignore
        lock.release()

        while is_running.value:  # type: ignore
            memory_usages.append(process.memory_full_info())
            sleep(self.current_run.experiment.memory_measure_interval)

        logging.debug("debug 7 -> gather monitoring data")

        # Gather process statistics
        self.output_cpu_usage(self.current_run, implementation, case, process.cpu_percent())
        self.output_memory_usages(self.current_run, implementation, case, memory_usages)
        self.output_storage_space(self.current_run, implementation, case, )

        # Wait for the cleanup to finish
        p.join()

        logging.debug("debug 9 -> process stopped")

    @staticmethod
    def run_experiment_case_synchronously(experiments_run: ExperimentsRun,
                                          implementation: BaseImplementation, case: ExperimentCase, lock: Condition,
                                          is_running: Value) -> None:
        try:
            logging.debug("debug 2 -> process started")

            # Empty the storage directories
            experiments_run.experiment.setup_directories()
            experiments_run.experiment.setup(implementation, case)

            # We are done, let the main process setup monitoring
            lock.acquire()
            logging.debug("debug 3 -> experiment setup finished")
            lock.notify()
            lock.wait()
            logging.debug("debug 5 -> start experiment")

            # And off we go
            experiments_run.experiment.start_measurements()
            experiments_run.experiment.run()
            experiments_run.experiment.stop_measurements()

            # We are done, notify the main process to stop monitoring
            logging.debug("debug 6 -> stop experiment")
            is_running.value = False  # type: ignore

            ExperimentsRunner.output_timings(experiments_run, implementation, case,
                                             experiments_run.experiment.pr)
            ExperimentsRunner.output_connections(experiments_run, implementation, case,
                                                 experiments_run.experiment.get_connections())

            # Cleanup
            logging.debug("debug 8 -> cleanup finished")
        except BaseException:
            ExperimentsRunner.output_error(experiments_run, implementation, case)
        finally:
            try:
                is_running.value = False  # type: ignore
                lock.notify()
                lock.release()
            except:
                pass

    @staticmethod
    def experiment_results_directory(experiments_run: ExperimentsRun) -> str:
        return path.join(OUTPUT_DIRECTORY,
                         experiments_run.experiment.get_name(),
                         experiments_run.device_name,
                         experiments_run.timestamp)

    @staticmethod
    def experiment_case_results_directory(experiments_run: ExperimentsRun, implementation: BaseImplementation, case: ExperimentCase):
        return path.join(ExperimentsRunner.experiment_results_directory(experiments_run),
                         implementation.get_name(),
                         case.name)

    @staticmethod
    def output_cpu_usage(experiments_run: ExperimentsRun, implementation: BaseImplementation, case: ExperimentCase,
                         cpu_usage: float) -> None:
        directory = ExperimentsRunner.experiment_case_results_directory(experiments_run, implementation, case)
        with open(path.join(directory, 'cpu.txt'), 'w') as file:
            file.write(str(cpu_usage))

    @staticmethod
    def output_error(experiments_run: ExperimentsRun, implementation: BaseImplementation, case: ExperimentCase) -> None:
        directory = ExperimentsRunner.experiment_case_results_directory(experiments_run, implementation, case)
        logging.error(traceback.format_exc())
        with open(path.join(directory, 'ERROR.txt'), 'w') as file:
            traceback.print_exc(file=file)

    @staticmethod
    def output_connections(experiments_run: ExperimentsRun, implementation: BaseImplementation, case: ExperimentCase,
                           connections: List[BaseConnection]) -> None:
        directory = ExperimentsRunner.experiment_case_results_directory(experiments_run, implementation, case)
        connections_to_csv(connections, path.join(directory, 'network.csv'))

    @staticmethod
    def output_memory_usages(experiments_run: ExperimentsRun, implementation: BaseImplementation, case: ExperimentCase,
                             memory_usages: List[Any]) -> None:
        directory = ExperimentsRunner.experiment_case_results_directory(experiments_run, implementation, case)
        with open(path.join(directory, 'memory.csv'), 'w') as file:
            writer = csv.DictWriter(file, fieldnames=[
                'rss', 'vms', 'shared', 'text', 'lib', 'data', 'dirty', 'uss', 'pss', 'swap'
            ])
            writer.writeheader()
            for row in memory_usages:
                writer.writerow(row._asdict())

    @staticmethod
    def output_storage_space(experiments_run: ExperimentsRun, implementation: BaseImplementation,
                             case: ExperimentCase) -> None:
        directory = ExperimentsRunner.experiment_case_results_directory(experiments_run, implementation, case)
        insurance_storage = experiments_run.experiment.get_insurance_storage_path()
        with open(path.join(directory, 'storage_insurance.csv'), 'w') as output:
            writer = csv.writer(output)
            writer.writerow(('filename', 'size'))
            for file in listdir(insurance_storage):
                size = path.getsize(path.join(insurance_storage, file))
                writer.writerow((file, size))

    @staticmethod
    def output_timings(experiments_run: ExperimentsRun, implementation: BaseImplementation, case: ExperimentCase,
                       profile: Profile) -> None:
        directory = ExperimentsRunner.experiment_case_results_directory(experiments_run, implementation, case)
        stats_file_path = path.join(directory, 'timings.txt')
        profile.dump_stats(stats_file_path)
        pstats_to_step_timings(stats_file_path,
                               path.join(directory, 'step_timings.csv'))
        pstats_to_csv(stats_file_path,
                      path.join(directory, 'timings.csv'))
        pstats_to_csv2(stats_file_path,
                       path.join(directory, 'timings2.csv'))

    def setup_logging(self):
        directory = self.experiment_results_directory(self.current_run)
        logging.basicConfig(filename=path.join(directory, 'log.log'), level=logging.INFO)


if __name__ == '__main__':
    runner = ExperimentsRunner()
    runner.run_base_experiments()
