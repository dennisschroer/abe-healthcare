from typing import List

from experiments.base_experiment import BaseExperiment
from experiments.runner.experiment_case import ExperimentCase


class PolicySizeExperiment(BaseExperiment):
    generated_file_amount = 1
    run_descriptions = {
        'setup_authsetup': 'once',
        'register_keygen': 'once',
        'encrypt': 'always',
        'update_keys': 'always',
        'data_update': 'never',
        'policy_update': 'never',
        'decrypt': 'always'
    }

    def __init__(self, cases: List[ExperimentCase] = None) -> None:
        if cases is None:
            attribute_pairs = list(map(lambda a: '(%s@AUTHORITY0 OR %s@AUTHORITY1)' % (a, a), [
                'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN'
            ]))
            cases = list(map(
                lambda size: ExperimentCase("size %d" % size,
                                            {'policy': ' AND '.join(attribute_pairs[:size])}),
                [1, 3, 5, 7, 9]
            ))
        super().__init__(cases)

    def setup(self):
        super().setup()
        self.read_policy = self.state.case.arguments['policy']
