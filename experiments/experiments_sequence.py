from experiments.base_experiment import BaseExperiment
from experiments.experiments_sequence_state import ExperimentsSequenceState


class ExperimentsSequence(object):
    """
    An ExperimentsSequence defines a single experiment and the amount of times it should be repeated. Furthermore, it is used
    to keep track of the state of the experiment: which implementation is currently used and which iteration are we running?
    """

    def __init__(self, experiment: BaseExperiment, amount: int) -> None:
        self.state = ExperimentsSequenceState()
        self.state.amount = amount
        self.experiment = experiment
        self.experiment.sequence_state = self.state
