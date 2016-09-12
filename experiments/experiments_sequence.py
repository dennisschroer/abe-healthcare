from typing import List

from experiments.base_experiment import BaseExperiment
from experiments.experiments_sequence_state import ExperimentsSequenceState
from shared.implementations.base_implementation import BaseImplementation
from shared.implementations.dacmacs13_implementation import DACMACS13Implementation
from shared.implementations.rd13_implementation import RD13Implementation
from shared.implementations.rw15_implementation import RW15Implementation
from shared.implementations.taac12_implementation import TAAC12Implementation

implementations = [
    DACMACS13Implementation(),
    RD13Implementation(),
    RW15Implementation(),
    TAAC12Implementation()
]  # type: List[BaseImplementation]


class ExperimentsSequence(object):
    """
    An ExperimentsSequence defines a single experiment and the amount of times it should be repeated. Furthermore, it is used
    to keep track of the state of the experiment: which implementation is currently used and which iteration are we running?
    """

    def __init__(self, experiment: BaseExperiment, amount: int) -> None:
        self.state = ExperimentsSequenceState()
        self.state.amount = amount
        self.experiment = experiment
