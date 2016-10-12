from typing import List

from experiments.base_experiment import BaseExperiment
from experiments.runner.experiment_case import ExperimentCase


class UserKeySizeExperiment(BaseExperiment):
    generated_file_amount = 0
    measurement_repeat = 1
    run_descriptions = {
        'setup_authsetup': 'once',
        'register_keygen': 'always',
        'encrypt': 'never',
        'update_keys': 'never',
        'data_update': 'never',
        'policy_update': 'never',
        'decrypt': 'never'
    }
    attribute_authority_descriptions = [  # type: List[Dict[str, Any]]
        {
            'name': 'AUTHORITY0',
            'attributes': list(map(lambda a: a + '@AUTHORITY0', [
                'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN', 'ELEVEN', 'TWELVE',
                'THIRTEEN', 'FOURTEEN', 'FIFTEEN', 'SIXTEEN', 'SEVENTEEN', 'EIGHTEEN', 'NINETEEN', 'TWENTY'
            ]))
        }
    ]
    user_descriptions = [  # type: List[Dict[str, Any]]
        {
            'gid': 'DOCTOR',
            'attributes': {
                'AUTHORITY0': []
            }
        },
    ]

    def __init__(self, cases: List[ExperimentCase] = None) -> None:
        if cases is None:
            attributes = self.attribute_authority_descriptions[0]['attributes']
            cases = list(map(
                lambda size: ExperimentCase("size %d" % (size + 1),
                                            {'user_keys': attributes[:size + 1]}),
                range(20)
            ))
        super().__init__(cases)

    def setup(self):
        super().setup()
        self.user_descriptions[0]['attributes']['AUTHORITY0'] = self.state.case.arguments['user_keys']
