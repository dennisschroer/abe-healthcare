import logging
from typing import List

from experiments.base_experiment import BaseExperiment
from experiments.experiment_case import ExperimentCase


class PolicySizeExperiment(BaseExperiment):
    def __init__(self, cases: List[ExperimentCase] = None) -> None:
        if cases is None:
            attributes = list(map(lambda a: a + '@AUTHORITY1', [
                'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN'
            ]))
            cases = list(map(
                lambda size: ExperimentCase(str(size + 1), {'policy': ' AND '.join(attributes[:size + 1])}),
                range(10)
            ))
            for case in cases:
                logging.debug(case.arguments)
        super().__init__(cases)

    def run(self):
        location = self.user_clients[0].encrypt_file(self.file_name,
                                                     self.current_state.current_case.arguments['policy'],
                                                     self.write_policy)
        self.user_clients[1].decrypt_file(location)
