from typing import List

from experiments.base_experiment import BaseExperiment
from experiments.experiment_case import ExperimentCase
from experiments.experiment_state import ExperimentProgress


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
                range(10)
            ))
        super().__init__(cases)

    def run_encrypt(self):
        self.set_progress(ExperimentProgress.encrypt)
        self.location = self.user_clients[0].encrypt_file(
            self.file_name,
            self.state.case.arguments['policy'],
            self.write_policy)
