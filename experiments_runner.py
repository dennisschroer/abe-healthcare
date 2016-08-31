import logging
from multiprocessing import Condition  # type: ignore
from multiprocessing import Process
from multiprocessing import Value
from os import makedirs
from os import path
from time import sleep

import psutil

from experiments.base_experiment import BaseExperiment
from experiments.experiment_output import OUTPUT_DIRECTORY, ExperimentOutput
from experiments.experiments_sequence import ExperimentsSequence
from experiments.file_size_experiment import FileSizeExperiment
from experiments.policy_size_experiment import PolicySizeExperiment
from shared.implementations.dacmacs13_implementation import DACMACS13Implementation
from shared.implementations.rd13_implementation import RD13Implementation
from shared.implementations.rw15_implementation import RW15Implementation
from shared.implementations.taac12_implementation import TAAC12Implementation

debug = False


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
        self.current_run = None  # type: ExperimentsSequence

    def run_base_experiments(self) -> None:
        self.run_experiments_run(ExperimentsSequence(BaseExperiment(), 2))

    def run_file_size_experiments(self) -> None:
        self.run_experiments_run(ExperimentsSequence(FileSizeExperiment(), 1))

    def run_policy_size_experiments(self) -> None:
        self.run_experiments_run(ExperimentsSequence(PolicySizeExperiment(), 1))

    def run_experiments_run(self, experiments_run: ExperimentsSequence) -> None:
        """
        Run the experiments as defined in the ExperimentsSequence and repeat it the amount defined in the ExperimentsSequence.
        :param experiments_run:
        """
        self.current_run = experiments_run

        # Create directories
        if not path.exists(ExperimentOutput.experiment_results_directory(self.current_run)):
            makedirs(ExperimentOutput.experiment_results_directory(self.current_run))

        # Setup logging
        self.setup_logging()

        logging.info("Device '%s' starting experiment '%s' with timestamp '%s', running %d times" % (
            experiments_run.device_name, experiments_run.experiment.get_name(), experiments_run.timestamp,
            experiments_run.amount))
        experiments_run.experiment.global_setup()
        logging.info("Global setup finished")

        for i in range(0, experiments_run.amount):
            self.current_run.iteration = i
            self.run_current_experiment()

        logging.info("Device '%s' finished experiment '%s' with timestamp '%s', current time: %s" % (
            experiments_run.device_name, experiments_run.experiment.get_name(), experiments_run.timestamp,
            experiments_run.current_time_formatted()))

    def run_current_experiment(self) -> None:
        """
        Run the experiment of the current run a single time.
        """
        for implementation in self.implementations:
            self.current_run.current_implementation = implementation
            for case in self.current_run.experiment.cases:
                self.current_run.current_case = case
                self.run_current_experiment_case()

    def run_current_experiment_case(self) -> None:
        """
        Run the current case with the current implementation of the current experiment.

        This is done by starting the experiment in a seperate process.
        """
        logging.info("=> Run %d/%d of %s, implementation=%s (%d/%d), case=%s (%d/%d)" % (
            self.current_run.iteration + 1,
            self.current_run.amount,
            self.current_run.experiment.get_name(),
            self.current_run.current_implementation.get_name(),
            self.implementations.index(self.current_run.current_implementation) + 1,
            len(self.implementations),
            self.current_run.current_case.name,
            self.current_run.experiment.cases.index(self.current_run.current_case) + 1,
            len(self.current_run.experiment.cases)
        ))

        # Create a lock
        lock = Condition()
        lock.acquire()

        # Create output directory
        output_directory = ExperimentOutput.experiment_case_iteration_results_directory(self.current_run)
        if not path.exists(output_directory):
            makedirs(output_directory)

        # Create a separate process
        is_running = Value('b', False)
        p = Process(target=self.run_experiment_case_synchronously,
                    args=(self.current_run, lock, is_running))

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
        ExperimentOutput.output_cpu_usage(self.current_run, process.cpu_percent())
        ExperimentOutput.output_memory_usages(self.current_run, memory_usages)
        ExperimentOutput.output_storage_space(self.current_run)

        # Wait for the cleanup to finish
        p.join()

        logging.debug("debug 9 -> process stopped")

    @staticmethod
    def run_experiment_case_synchronously(experiments_run: ExperimentsSequence, lock: Condition, is_running: Value) -> None:
        """
        Run the experiment in this process.
        :param experiments_run: The current running experiment
        :param lock: A lock, required for synchronization
        :param is_running: A flag indicating whether the experiment is running
        """
        try:
            logging.debug("debug 2 -> process started")

            # Empty the storage directories
            experiments_run.experiment.setup_directories()
            experiments_run.experiment.setup(experiments_run.current_implementation, experiments_run.current_case)

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

            ExperimentOutput.output_timings(experiments_run, experiments_run.experiment.pr)
            ExperimentOutput.output_connections(experiments_run, experiments_run.experiment.get_connections())

            # Cleanup
            logging.debug("debug 8 -> cleanup finished")
        except BaseException:
            ExperimentOutput.output_error(experiments_run)
        finally:
            try:
                is_running.value = False  # type: ignore
                lock.notify()
                lock.release()
            except:
                pass

    def setup_logging(self) -> None:
        """
        Setup logging for the current experiments run.
        """
        directory = ExperimentOutput.experiment_results_directory(self.current_run)
        logging.basicConfig(filename=path.join(directory, 'log.log'), level=logging.INFO)


if __name__ == '__main__':
    runner = ExperimentsRunner()
    runner.run_base_experiments()
