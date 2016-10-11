from typing import List

from experiments.policy_size_experiment import PolicySizeExperiment
from experiments.runner.experiment_case import ExperimentCase


class DisjunctivePolicySizeExperiment(PolicySizeExperiment):
    def __init__(self, cases: List[ExperimentCase] = None) -> None:
        if cases is None:
            attribute_pairs = list(map(lambda a: '(%s@AUTHORITY0 AND %s@AUTHORITY1)' % (a, a), [
                'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN'
            ]))
            cases = list(map(
                lambda size: ExperimentCase("size %d" % (size + 1),
                                            {'policy': ' OR '.join(attribute_pairs[:size + 1])}),
                [2 * x for x in range(5)]
            ))
        super().__init__(cases)
