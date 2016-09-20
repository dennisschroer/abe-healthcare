import datetime
import socket

from shared.implementations.base_implementation import BaseImplementation

TIMESTAMP_FORMAT = '%Y-%m-%d %H-%M-%S'


class ExperimentsSequenceState(object):
    def __init__(self):
        self._timestamp = None  # type:str
        self._device_name = None  # type:str
        self.amount = None  # type: int

        self.iteration = None  # type: int
        self.implementation = None  # type: BaseImplementation

    def __repr__(self):
        return "ExperimentsSequenceState[implementation=%s, amount=%s, iteration=%s]" % (
            self.implementation.get_name(), self.amount, self.iteration)

    @property
    def device_name(self) -> str:
        """
        Gets the device name of the device running these experiments.
        :return:
        """
        if self._device_name is None:
            self._device_name = socket.gethostname()
        return self._device_name

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
