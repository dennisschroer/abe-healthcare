from experiments.experiment_case import ExperimentCase
from experiments.enum.measurement_type import MeasurementType
from shared.implementations.base_implementation import BaseImplementation


class ExperimentsSequenceState(object):
    def __init__(self):
        self.current_implementation = None  # type: BaseImplementation
        self.current_case = None  # type: ExperimentCase
        self.iteration = None  # type: int
        self.measurement_type = None  # type: MeasurementType
