import datetime
import socket

from experiments.base_experiment import BaseExperiment

TIMESTAMP_FORMAT = '%Y-%m-%d %H-%M-%S'


class ExperimentsRun(object):
    def __init__(self,  experiment: BaseExperiment, amount: int):
        self.amount = amount
        self.experiment = experiment

        self._timestamp = None  # type:str
        self._device_name = None  # type:str

    @property
    def timestamp(self) -> str:
        if self._timestamp is None:
            self._timestamp = datetime.datetime.now().strftime(TIMESTAMP_FORMAT)
        return self._timestamp

    @property
    def device_name(self) -> str:
        if self._device_name is None:
            self._device_name = socket.gethostname()
        return self._device_name
