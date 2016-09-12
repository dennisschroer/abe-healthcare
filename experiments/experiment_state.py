from enum import Enum
from multiprocessing import Value

from experiments.enum.measurement_type import MeasurementType
from experiments.experiment_case import ExperimentCase


class ExperimentProgress(Enum):
    running = 0

    stopping = 10


class ExperimentState(object):
    def __init__(self):
        self.case = None  # type: ExperimentCase
        self.measurement_type = None  # type: MeasurementType
        self.progress = Value('i')
