import cProfile
from os import path, makedirs
from typing import List, Dict, Any

from shared.connection.base_connection import BaseConnection
from shared.implementations.base_implementation import BaseImplementation

PROFILE_DATA_DIRECTORY = 'data/profile'


class ExperimentCase(object):
    def __init__(self, name: str, arguments: Dict[str, Any]) -> None:
        self.name = name
        self.arguments = arguments


class BaseExperiment(object):
    def __init__(self, implementation: BaseImplementation) -> None:
        self.pr = cProfile.Profile()
        self.implementation = implementation
        self.cases = list()  # type: List[ExperimentCase]

        if not path.exists(PROFILE_DATA_DIRECTORY):
            makedirs(PROFILE_DATA_DIRECTORY)

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
