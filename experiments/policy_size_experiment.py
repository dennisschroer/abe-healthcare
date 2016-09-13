import logging
from typing import List

from experiments.base_experiment import BaseExperiment
from experiments.experiment_case import ExperimentCase


class PolicySizeExperiment(BaseExperiment):
    def __init__(self, cases: List[ExperimentCase] = None) -> None:
        if cases is None:
            attribute_pairs = list(map(lambda a: '(%s@AUTHORITY1 OR %s@AUTHORITY2)' % (a, a), [
                'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN'
            ]))
            cases = list(map(
                lambda size: ExperimentCase(str(size + 1), {'policy': ' AND '.join(attribute_pairs[:size + 1])}),
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
