import cProfile
import os
from typing import List, Dict, Any

import shutil

from shared.connection.base_connection import BaseConnection
from shared.implementations.base_implementation import BaseImplementation


class ExperimentCase(object):
    def __init__(self, name: str, arguments: Dict[str, Any]) -> None:
        self.name = name
        self.arguments = arguments


class BaseExperiment(object):
    def __init__(self, implementation: BaseImplementation) -> None:
        self.pr = cProfile.Profile()
        self.implementation = implementation  # type: BaseImplementation
        self.cases = list()  # type: List[ExperimentCase]
        self.device_name = None  # type: str
        self.timestamp = None  # type: str

    def global_setup(self) -> None:
        """
        Setup all case independent things for this experiment, like generating random input files.
        """
        raise NotImplementedError()

    def setup(self, case: ExperimentCase):
        """
        Setup all case dependant things for this experiment.
        :return:
        """
        raise NotImplementedError()

    def start_measurements(self) -> None:
        """
        Start the measurements. These are only part of the measurements, namely the one which need to run
        in the experiment process.
        :return:
        """
        self.pr.enable()

    def stop_measurements(self) -> None:
        """
        Stop the measurements.
        """
        self.pr.disable()

    def run(self, case: ExperimentCase) -> None:
        raise NotImplementedError()

    def get_connections(self) -> List[BaseConnection]:
        """
        Get all connections used in this experiment of which the usage should be outputted.
        :return: A list of connections
        """
        raise NotImplementedError()

    def get_name(self):
        return self.__class__.__name__

    def setup_directories(self):
        # Empty storage directories
        if os.path.exists(self.get_user_client_storage_path()):
            shutil.rmtree(self.get_user_client_storage_path())
        if os.path.exists(self.get_insurance_storage_path()):
            shutil.rmtree(self.get_insurance_storage_path())

        # Create directories
        if not os.path.exists(self.get_experiment_input_path()):
            os.makedirs(self.get_experiment_input_path())
        os.makedirs(self.get_user_client_storage_path())
        os.makedirs(self.get_insurance_storage_path())

    def get_experiment_storage_base_path(self):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            '../data/experiments/%s' % self.get_name())

    def get_experiment_input_path(self):
        return os.path.join(self.get_experiment_storage_base_path(), 'input')

    def get_user_client_storage_path(self):
        return os.path.join(self.get_experiment_storage_base_path(), 'client')

    def get_insurance_storage_path(self):
        return os.path.join(self.get_experiment_storage_base_path(), 'insurance')
