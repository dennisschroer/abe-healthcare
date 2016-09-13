import logging
from multiprocessing import Process
from os import makedirs
from os import path
from time import sleep

import psutil

from experiments.base_experiment import BaseExperiment
from experiments.enum.implementations import implementations
from experiments.enum.measurement_type import MeasurementType
from experiments.experiment_output import OUTPUT_DIRECTORY
from experiments.experiment_state import ExperimentProgress
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
        self.psutil_process = None  # type: psutil.Process
        self.experiment_process = None  # type: Process
        self.memory_usages = None  # type: List[dict]

    def run_base_experiments(self) -> None:
        self.run_experiments_sequence(ExperimentsSequence(BaseExperiment(), 20))

    def run_file_size_experiments(self) -> None:
        self.run_experiments_sequence(ExperimentsSequence(FileSizeExperiment(), 1))

    def run_policy_size_experiments(self) -> None:
        self.run_experiments_sequence(ExperimentsSequence(PolicySizeExperiment(), 10))

    def run_experiments_sequence(self, experiments_sequence: ExperimentsSequence) -> None:
        """
        Run the experiments as defined in the ExperimentsSequence and repeat it the amount defined in the ExperimentsSequence.
        :param experiments_sequence:
        """
        self.current_sequence = experiments_sequence
        current_state = self.current_sequence.state

        # Create directories
        if not path.exists(self.current_sequence.experiment.output.experiment_results_directory()):
            makedirs(self.current_sequence.experiment.output.experiment_results_directory())

        # Setup logging
        self.setup_logging()
        self.log_experiment_start()

        self.current_sequence.experiment.global_setup()
        logging.info("Global setup finished")

        for i in range(0, current_state.amount):
            current_state.iteration = i

            for implementation in implementations:
                current_state.implementation = implementation

                if i == 0:
                    # We need to do some cleanup first
                    experiments_sequence.experiment.setup_directories()
                    experiments_sequence.experiment.implementation_setup()

                self.run_current_experiment_with_current_state()

        logging.info("Device '%s' finished experiment '%s' with timestamp '%s', current time: %s" % (
            current_state.device_name,
            experiments_sequence.experiment.get_name(),
            current_state.timestamp,
            current_state.current_time_formatted()))

    def log_experiment_start(self):
        current_state = self.current_sequence.state
        logging.info("Device '%s' starting experiment '%s' with timestamp '%s', running %d times" % (
            current_state.device_name,
            self.current_sequence.experiment.get_name(),
            current_state.timestamp,
            current_state.amount))
        logging.info("Run configurations: %s" % str(self.current_sequence.experiment.run_descriptions))
        logging.info(
            "Authority descriptions: %s" % str(self.current_sequence.experiment.attribute_authority_descriptions))
        logging.info("User descriptions: %s" % str(self.current_sequence.experiment.user_descriptions))
        logging.info("File size: %s" % str(self.current_sequence.experiment.file_size))
        logging.info("Read policy: %s" % str(self.current_sequence.experiment.read_policy))
        logging.info("Write policy: %s" % str(self.current_sequence.experiment.write_policy))
        logging.info("Cases: %s" % str(self.current_sequence.experiment.cases))

    def log_current_experiment(self):
        logging.info("=> Run %d/%d of %s, implementation=%s (%d/%d)" % (
            self.current_sequence.state.iteration + 1,
            self.current_sequence.state.amount,
            self.current_sequence.experiment.get_name(),
            self.current_sequence.state.implementation.get_name(),
            implementations.index(self.current_sequence.state.implementation) + 1,
            len(implementations)
        ))

    def run_current_experiment_with_current_state(self) -> None:
        """
        Run the current case with the current implementation of the current experiment.

        This is done by starting the experiment in a separate process.
        """
        self.log_current_experiment()

        self.current_sequence.experiment.sequence_state = self.current_sequence.state

        self.current_sequence.experiment.sync_lock.acquire()

        self.experiment_process = Process(name=self.current_sequence.experiment.get_name(),
                                          target=self.current_sequence.experiment.run)
        self.experiment_process.start()

        # Initialize variables
        self.memory_usages = list()

        # Wait untill the state of the experiment is correct
        self.sync()

        # Setup is finished
        while self.current_sequence.experiment.state.progress != ExperimentProgress.stopping:
            self.start_measurements()

            while self.current_sequence.experiment.state.progress == ExperimentProgress.running:
                self.run_measurement()
                sleep(self.current_sequence.experiment.memory_measure_interval)

            self.finish_measurements()
            # Wait for the state to be updated
            self.sync()

        self.experiment_process.join()

    def start_measurements(self):
        logging.debug("Runner.start about to wait")
        # Wait untill setup is finished
        self.sync()
        # Setup is finished, start monitoring
        if self.current_sequence.experiment.state.measurement_type in (MeasurementType.cpu, MeasurementType.memory):
            self.psutil_process = psutil.Process(self.experiment_process.pid)
            self.psutil_process.cpu_percent()

    def run_measurement(self):
        if self.current_sequence.experiment.state.measurement_type is MeasurementType.memory:
            self.memory_usages.append(self.psutil_process.memory_full_info())

    def finish_measurements(self):
        logging.debug("Runner.finish")
        if self.current_sequence.experiment.state.measurement_type == MeasurementType.cpu:
            self.current_sequence.experiment.output.output_cpu_usage(self.psutil_process.cpu_percent())
        if self.current_sequence.experiment.state.measurement_type == MeasurementType.memory:
            self.current_sequence.experiment.output.output_memory_usages(self.memory_usages)
        # Wait for the experiment to output the result
        self.sync()

    def sync(self):
        """
        Synchronize with the experiment's process. This happens at three moments:
        - When the state of the next experiment is set
        - When the setup is done and the measurements should start
        - When the results are saved and before the state is updated for the next experiment
        """
        logging.debug("Runner.sync")
        self.current_sequence.experiment.sync_lock.wait()
        self.current_sequence.experiment.sync_lock.acquire()

    def setup_logging(self) -> None:
        """
        Setup logging for the current experiments run.
        """
        directory = self.current_sequence.experiment.output.experiment_results_directory()
        print("Logging to %s" % path.join(directory, 'log.log'))
        logging.basicConfig(filename=path.join(directory, 'log.log'), level=logging.DEBUG)


if __name__ == '__main__':
    runner = ExperimentsRunner()
    runner.run_base_experiments()
    # runner.run_policy_size_experiments()
