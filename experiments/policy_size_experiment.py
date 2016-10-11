from typing import List

from experiments.base_experiment import BaseExperiment
from experiments.runner.experiment_case import ExperimentCase


class PolicySizeExperiment(BaseExperiment):
    run_descriptions = {
        'setup_authsetup': 'once',
        'register_keygen': 'once'
    }

    def __init__(self, cases: List[ExperimentCase] = None) -> None:
        if cases is None:
            attribute_pairs = list(map(lambda a: '(%s@AUTHORITY0 OR %s@AUTHORITY1)' % (a, a), [
                'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN'
            ]))
            cases = list(map(
                lambda size: ExperimentCase("size %d" % (size + 1),
                                            {'policy': ' AND '.join(attribute_pairs[:size + 1])}),
                [2 * x for x in range(5)]
            ))
        super().__init__(cases)

    def setup(self):
        super().setup()
        self.read_policy = self.state.case.arguments['policy']
