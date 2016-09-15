from enum import Enum
from multiprocessing import Manager  # type: ignore

from experiments.enum.measurement_type import MeasurementType
from experiments.experiment_case import ExperimentCase


class ExperimentProgress(Enum):
    experiment_setup = 0
    experiment_starting = 1
    setup = 2
    authsetup = 3
    register = 4
    keygen = 5
    encrypt = 6
    decryption_keys = 7
    decrypt = 8
    stopping = 10


class ExperimentState(object):
    def __init__(self):
        manager = Manager()
        self._dict = manager.dict()
        self.case = None  # type: ExperimentCase
        self.measurement_type = None  # type: MeasurementType
        self.progress = None  # type: ExperimentProgress

    @property
    def case(self):
        return self._dict['case']

    @property
    def measurement_type(self):
        return self._dict['measurement_type']

    @property
    def progress(self):
        return self._dict['progress']

    @case.setter  # type: ignore
    def case(self, value):
        self._dict['case'] = value

    @measurement_type.setter  # type: ignore
    def measurement_type(self, value):
        self._dict['measurement_type'] = value

    @progress.setter  # type: ignore
    def progress(self, value):
        self._dict['progress'] = value

    def __repr__(self):
        return "ExperimentState[case=%s, measurement_type=%s, progress=%s]" % (
            self.case, self.measurement_type, self.progress)
