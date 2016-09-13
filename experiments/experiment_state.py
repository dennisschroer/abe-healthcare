from enum import Enum
from multiprocessing import Value

from multiprocessing import Manager

from experiments.enum.measurement_type import MeasurementType
from experiments.experiment_case import ExperimentCase


class ExperimentProgress(Enum):
    setup = 0
    running = 1
    stopping = 2


class ExperimentState(object):
    def __init__(self):
        manager = Manager()
        self._dict = manager.dict()
        self.case = None  # type: ExperimentCase
        self.measurement_type = None  # type: MeasurementType
        self.progress = None

    @property
    def case(self):
        return self._dict['case']

    @property
    def measurement_type(self):
        return self._dict['measurement_type']

    @property
    def progress(self):
        return self._dict['progress']

    @case.setter
    def case(self, value):
        self._dict['case'] = value

    @measurement_type.setter
    def measurement_type(self, value):
        self._dict['measurement_type'] = value

    @progress.setter
    def progress(self, value):
        self._dict['progress'] = value

    def __repr__(self):
        return "ExperimentState[case=%s, measurement_type=%s, progress=%s]" % (self.case, self.measurement_type, self.progress)
