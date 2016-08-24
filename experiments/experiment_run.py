import datetime
import socket

from experiments.base_experiment import BaseExperiment
from experiments.base_experiment import ExperimentCase
from shared.implementations.base_implementation import BaseImplementation

TIMESTAMP_FORMAT = '%Y-%m-%d %H-%M-%S'


class ExperimentsRun(object):
    def __init__(self, experiment: BaseExperiment, amount: int):
        self.amount = amount
        self.experiment = experiment
        self.current_implementation = None  # type:BaseImplementation
        self.current_case = None  # type: ExperimentCase
        self.iteration = None # type: int

        self._timestamp = None  # type:str
        self._device_name = None  # type:str

    @property
    def timestamp(self) -> str:
        if self._timestamp is None:
            self._timestamp = self.current_time()
        return self._timestamp

    def current_time(self):
        return datetime.datetime.now().strftime(TIMESTAMP_FORMAT)

    @property
    def device_name(self) -> str:
        if self._device_name is None:
            self._device_name = socket.gethostname()
        return self._device_name
