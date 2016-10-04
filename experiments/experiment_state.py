import datetime
import socket

from experiments.enum.abe_step import ABEStep
from experiments.enum.measurement_type import MeasurementType
from experiments.experiment_case import ExperimentCase
from shared.implementations.base_implementation import BaseImplementation

TIMESTAMP_FORMAT = '%Y-%m-%d %H-%M-%S'


class ExperimentState(object):
    def __init__(self):
        self._timestamp = None  # type:str
        self._device_name = None  # type:str

        self.implementation = None  # type: BaseImplementation
        self.iteration = None  # type: int
        self.case = None  # type: ExperimentCase
        self.measurement_type = None  # type: MeasurementType
        self.abe_step = None  # type: ABEStep

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

    def __repr__(self):
        return "ExperimentState[case=%s, measurement_type=%s, progress=%s]" % (
            self.case, self.measurement_type, self.progress)
