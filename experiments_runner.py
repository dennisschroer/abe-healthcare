import cProfile
import logging
from multiprocessing import Condition  # type: ignore
from multiprocessing import Process
from multiprocessing import Value
from os import makedirs
from os import path
from time import sleep

import psutil

from experiments.base_experiment import BaseExperiment
from experiments.enum.measurement_type import MeasurementType
from experiments.experiment_output import OUTPUT_DIRECTORY, ExperimentOutput
from experiments.experiments_sequence import ExperimentsSequence
from experiments.file_size_experiment import FileSizeExperiment
from experiments.policy_size_experiment import PolicySizeExperiment


class ExperimentsRunner(object):
    """
    Runner responsible for running the experiments and outputting the measurements.
    """

    def __init__(self) -> None:
        if not path.exists(OUTPUT_DIRECTORY):
            makedirs(OUTPUT_DIRECTORY)

        self._timestamp = None  # type: str
        self._device_name = None  # type: str
        self.current_sequence = None  # type: ExperimentsSequence

    def run_base_experiments(self) -> None:
        self.run_experiments_sequence(ExperimentsSequence(BaseExperiment(), 20))

    def run_file_size_experiments(self) -> None:
        self.run_experiments_sequence(ExperimentsSequence(FileSizeExperiment(), 1))

    def run_policy_size_experiments(self) -> None:
        self.run_experiments_sequence(ExperimentsSequence(PolicySizeExperiment(), 1))

    def run_experiments_sequence(self, experiments_sequence: ExperimentsSequence) -> None:
        """
        Run the experiments as defined in the ExperimentsSequence and repeat it the amount defined in the ExperimentsSequence.
        :param experiments_sequence:
        """
        self.current_sequence = experiments_sequence

        # Create directories
        if not path.exists(ExperimentOutput.experiment_results_directory(self.current_sequence)):
            makedirs(ExperimentOutput.experiment_results_directory(self.current_sequence))

        # Setup logging
        self.setup_logging()

        logging.info("Device '%s' starting experiment '%s' with timestamp '%s', running %d times" % (
            experiments_sequence.device_name, experiments_sequence.experiment.get_name(),
            experiments_sequence.timestamp,
            experiments_sequence.amount))
        experiments_sequence.experiment.global_setup()
        logging.info("Global setup finished")

        for i in range(0, experiments_sequence.amount):
            self.current_sequence.state.iteration = i
            print("%d/%d" % (self.current_sequence.state.iteration, experiments_sequence.amount))
            self.run_current_experiment()

        logging.info("Device '%s' finished experiment '%s' with timestamp '%s', current time: %s" % (
            experiments_sequence.device_name, experiments_sequence.experiment.get_name(),
            experiments_sequence.timestamp,
            experiments_sequence.current_time_formatted()))

    def run_current_experiment(self) -> None:
        """
        Run the experiment of the current run a single time.
        """
        for implementation in self.current_sequence.implementations:
            self.current_sequence.state.current_implementation = implementation
            for case in self.current_sequence.experiment.cases:
                self.current_sequence.state.current_case = case
                for measurement_type in MeasurementType:  # type:ignore
                    self.current_sequence.state.measurement_type = measurement_type
                    self.run_current_experiment_case()

    def run_current_experiment_case(self) -> None:
        """
        Run the current case with the current implementation of the current experiment.

        This is done by starting the experiment in a seperate process.
        """
        logging.info("=> Run %d/%d of %s, implementation=%s (%d/%d), case=%s (%d/%d), measurement=%s" % (
            self.current_sequence.state.iteration + 1,
            self.current_sequence.amount,
            self.current_sequence.experiment.get_name(),
            self.current_sequence.state.current_implementation.get_name(),
            self.current_sequence.implementations.index(self.current_sequence.state.current_implementation) + 1,
            len(self.current_sequence.implementations),
            self.current_sequence.state.current_case.name,
            self.current_sequence.experiment.cases.index(self.current_sequence.state.current_case) + 1,
            len(self.current_sequence.experiment.cases),
            self.current_sequence.state.measurement_type
        ))

        # Create a lock
        lock = Condition()
        lock.acquire()
        is_running = Value('b', False)

        # Create output directory
        output_directory = ExperimentOutput.experiment_case_iteration_results_directory(self.current_sequence)
        if not path.exists(output_directory):
            makedirs(output_directory)

        # Initialize variables
        memory_usages = list()

        # Create a separate process
        p = Process(target=self.run_experiment_case_synchronously,
                    args=(self.current_sequence, lock, is_running))

        logging.debug("debug 1 -> start process")

        # Start the process
        p.start()

        # Wait until the setup of the experiment is finished
        lock.wait()

        logging.debug("debug 4 -> start monitoring")

        # Setup is finished, start monitoring
        if self.current_sequence.state.measurement_type in (MeasurementType.cpu, MeasurementType.memory):
            process = psutil.Process(p.pid)  # type: ignore
            process.cpu_percent()

        # Release the lock, signaling the experiment to start, and wait for the experiment to finish
        lock.notify()
        is_running.value = True  # type: ignore
        lock.release()

        while is_running.value:  # type: ignore
            if self.current_sequence.state.measurement_type is MeasurementType.memory:
                memory_usages.append(process.memory_full_info())
            sleep(self.current_sequence.experiment.memory_measure_interval)

        logging.debug("debug 7 -> gather monitoring data")

        # Gather process statistics
        if self.current_sequence.state.measurement_type is MeasurementType.cpu:
            ExperimentOutput.output_cpu_usage(self.current_sequence, process.cpu_percent())
        if self.current_sequence.state.measurement_type is MeasurementType.memory:
            ExperimentOutput.output_memory_usages(self.current_sequence, memory_usages)
        if self.current_sequence.state.measurement_type is MeasurementType.storage_and_network:
            ExperimentOutput.output_storage_space(self.current_sequence)

        # Wait for the cleanup to finish
        p.join()

        logging.debug("debug 9 -> process stopped")

    @staticmethod
    def run_experiment_case_synchronously(experiments_sequence: ExperimentsSequence, lock: Condition,
                                          is_running: Value) -> None:
        """
        Run the experiment in this process.
        :param experiments_sequence: The current running experiment
        :param lock: A lock, required for synchronization
        :param is_running: A flag indicating whether the experiment is running
        """
        # noinspection PyBroadException
        try:
            logging.debug("debug 2 -> process started")

            # Empty the storage directories
            experiments_sequence.experiment.setup_directories()
            experiments_sequence.experiment.setup(experiments_sequence.state)

            # Setup variables
            pr = cProfile.Profile()

            # We are done, let the main process setup monitoring
            lock.acquire()
            logging.debug("debug 3 -> experiment setup finished")
            lock.notify()
            lock.wait()
            logging.debug("debug 5 -> start experiment")

            # And off we go
            if experiments_sequence.state.measurement_type == MeasurementType.timings:
                pr.enable()
            experiments_sequence.experiment.run()
            if experiments_sequence.state.measurement_type == MeasurementType.timings:
                pr.disable()

            # We are done, notify the main process to stop monitoring
            logging.debug("debug 6 -> stop experiment")
            is_running.value = False  # type: ignore

            if experiments_sequence.state.measurement_type == MeasurementType.timings:
                ExperimentOutput.output_timings(experiments_sequence, pr)
            if experiments_sequence.state.measurement_type == MeasurementType.storage_and_network:
                ExperimentOutput.output_connections(experiments_sequence,
                                                    experiments_sequence.experiment.get_connections())

            # Cleanup
            logging.debug("debug 8 -> cleanup finished")
        except:
            ExperimentOutput.output_error(experiments_sequence)
        finally:
            # noinspection PyBroadException
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
        directory = ExperimentOutput.experiment_results_directory(self.current_sequence)
        logging.basicConfig(filename=path.join(directory, 'log.log'), level=logging.INFO)


if __name__ == '__main__':
    runner = ExperimentsRunner()
    runner.run_base_experiments()
