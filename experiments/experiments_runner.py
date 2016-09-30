import logging
from os import makedirs
from os import path

from experiments.base_experiment import BaseExperiment


class ExperimentsRunner(object):
    """
    Runner responsible for running the experiments and outputting the measurements.
    """

    def __init__(self) -> None:
        self.current_experiment = None  # type: BaseExperiment

    def run_experiment(self, experiment: BaseExperiment) -> None:
        """
        Run the given experiment.
        :param experiment: The experiment to run.
        """
        self.current_experiment = experiment

        # Create directories
        if not path.exists(experiment.output.experiment_results_directory()):
            makedirs(experiment.output.experiment_results_directory())

        # Setup logging
        self.setup_logging()
        self.log_experiment_start()

        # Setup the experiment
        experiment.global_setup()
        logging.info("Global setup finished")

        self.current_experiment.run()

        self.log_experiment_finish()

    def log_experiment_start(self):
        logging.info("Device '%s' starting experiment '%s' with timestamp '%s', running %d times" % (
            self.current_experiment.state.device_name,
            self.current_experiment.get_name(),
            self.current_experiment.state.timestamp,
            self.current_experiment.measurement_repeat))
        logging.info("Run configurations: %s" % str(self.current_experiment.run_descriptions))
        logging.info("Measure interval: %s" % str(self.current_experiment.memory_measure_interval))
        logging.info(
            "Authority descriptions: %s" % str(self.current_experiment.attribute_authority_descriptions))
        logging.info("User descriptions: %s" % str(self.current_experiment.user_descriptions))
        logging.info("File size: %s" % str(self.current_experiment.encrypted_file_size))
        logging.info("Read policy: %s" % str(self.current_experiment.read_policy))
        logging.info("Write policy: %s" % str(self.current_experiment.write_policy))
        logging.info("Cases: %s" % str(self.current_experiment.cases))
        logging.info("Measurements: %s" % str(self.current_experiment.measurement_types))

    def log_experiment_finish(self):
        logging.info("Device '%s' finished experiment '%s' with timestamp '%s', current time: %s" % (
            self.current_experiment.state.device_name,
            self.current_experiment.get_name(),
            self.current_experiment.state.timestamp,
            self.current_experiment.state.current_time_formatted()))

    def setup_logging(self) -> None:
        """
        Setup logging for the current experiments run.
        """
        directory = self.current_experiment.output.experiment_results_directory()
        [logging.root.removeHandler(handler) for handler in logging.root.handlers[:]]
        logging.basicConfig(filename=path.join(directory, 'log.log'), level=logging.INFO)
        print("Logging to %s" % path.join(directory, 'log.log'))
