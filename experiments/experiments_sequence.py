import datetime
import socket

from experiments.base_experiment import BaseExperiment
from experiments.base_experiment import ExperimentCase
from shared.implementations.base_implementation import BaseImplementation

TIMESTAMP_FORMAT = '%Y-%m-%d %H-%M-%S'


class ExperimentsSequence(object):
    """
    An ExperimentsSequence defines a single experiment and the amount of times it should be repeated. Furthermore, it is used
    to keep track of the state of the experiment: which implementation is currently used and which iteration are we running?
    """
    def __init__(self, experiment: BaseExperiment, amount: int) -> None:
        self.amount = amount
        self.experiment = experiment
        self.current_implementation = None  # type:BaseImplementation
        self.current_case = None  # type: ExperimentCase
        self.iteration = None  # type: int

        self._timestamp = None  # type:str
        self._device_name = None  # type:str

    @property
    def timestamp(self) -> str:
        """
        Gets the timestamp for this experiments run.
        """
        if self._timestamp is None:
            self._timestamp = self.current_time_formatted()
        return self._timestamp

    @staticmethod
    def current_time_formatted() -> str:
        """
        Return the current time, formatted as a string
        :return:
        """
        return datetime.datetime.now().strftime(TIMESTAMP_FORMAT)

    @property
    def device_name(self) -> str:
        """
        Gets the device name of the device running these experiments.
        :return:
        """
        if self._device_name is None:
            self._device_name = socket.gethostname()
        return self._device_name
