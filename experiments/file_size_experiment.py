from typing import List

from experiments.base_experiment import BaseExperiment
from experiments.runner.experiment_case import ExperimentCase


class FileSizeExperiment(BaseExperiment):
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
    generated_file_sizes = [
        1,
        2 ** 10,
        2 ** 20,
        10 * (2 ** 20),
        50 * (2 ** 20),
        2 ** 30
    ]

    def __init__(self, cases: List[ExperimentCase] = None) -> None:
        if cases is None:
            cases = list(map(lambda size: ExperimentCase(size, {'file_size': size}), self.generated_file_sizes))
        super().__init__(cases)

    def setup(self):
        super().setup()
        self.encrypted_file_size = self.state.case.arguments['file_size']
