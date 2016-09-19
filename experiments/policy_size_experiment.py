import logging
from typing import List

from experiments.base_experiment import BaseExperiment
from experiments.experiment_case import ExperimentCase


class PolicySizeExperiment(BaseExperiment):
    run_descriptions = {
        # Can be 'always' or 'once'
        # When 'always', it is run in the run() method
        # When 'once', it is run during global setup and loaded in the run() method
        'setup_authsetup': 'once',
        'register_keygen': 'once',
        'encrypt_decrypt': 'always'
    }

    def __init__(self, cases: List[ExperimentCase] = None) -> None:
        if cases is None:
            attribute_pairs = list(map(lambda a: '(%s@AUTHORITY1 OR %s@AUTHORITY2)' % (a, a), [
                'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN'
            ]))
            cases = list(map(
                lambda size: ExperimentCase("size %d" % (size + 1), {'policy': ' AND '.join(attribute_pairs[:size + 1])}),
                range(10)
            ))
            # for case in cases:
            #     logging.debug(str(case.arguments))
        super().__init__(cases)

    def run_encrypt(self):
        self.location = self.user_clients[0].encrypt_file(
            self.file_name,
            self.state.case.arguments['policy'],
            self.write_policy)
