from typing import List

from experiments.base_experiment import BaseExperiment
from experiments.experiment_case import ExperimentCase


class AuthoritiesAmountExperiment(BaseExperiment):
    attribute_authority_descriptions = []
    user_descriptions = [  # type: List[Dict[str, Any]]
        {
            'gid': 'BOB',
            'attributes': {}
        },
        {
            'gid': 'DOCTOR',
            'attributes': {}
        },
    ]

    def __init__(self, cases: List[ExperimentCase] = None) -> None:
        assert self.run_descriptions['setup_authsetup'] is not 'once', \
            'Auth setup needs to run always in this experiment'

        if cases is None:
            cases = list(map(
                lambda amount: ExperimentCase(
                    "amount %d" % amount,
                    {
                        'amount': amount,
                        'policy': self._generate_policy(amount)
                    }
                ),
                [2, 4, 8, 16]
            ))
        super().__init__(cases)

    def _generate_policy(self, amount: int) -> str:
        """
        Generate a policy with a fixed size which uses attributes from the given amount of authorities.
        """
        attribute_names = ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT']
        attributes = ['%s@AUTHORITY%d' % (attribute_names[i % len(attribute_names)], i % amount) for i in range(16)]
        return ' AND '.join(attributes)

    def setup(self):
        super().setup()
        # Base amount of authorities on the current case
        self.attribute_authority_descriptions = list(map(
            lambda index: {
                'name': 'AUTHORITY%d' % index,
                'attributes': list(map(lambda a: a + ('@AUTHORITY%d' % index), [
                    'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT'
                ]))
            },
            range(self.state.case.arguments['amount'])
        ))
        # Base user keys on the current case
        self.user_descriptions[1]['attributes'] = {
            'AUTHORITY%d' % index: self.attribute_authority_descriptions[index]['attributes']
            for index
            in range(self.state.case.arguments['amount'])
            }

    def run_encrypt(self):
        self.location = self.user_clients[0].encrypt_file(
            self.file_name,
            self.state.case.arguments['policy'],
            self.write_policy)
