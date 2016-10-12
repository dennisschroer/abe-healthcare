from typing import Any
from typing import Dict
from typing import List

from experiments.base_experiment import BaseExperiment
from experiments.runner.experiment_case import ExperimentCase


class AuthoritiesAmountExperiment(BaseExperiment):
    generated_file_amount = 1
    attribute_authority_descriptions = []  # type: List[Dict[str, Any]]
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
        if cases is None:
            cases = list(map(
                lambda amount: ExperimentCase(
                    "amount %d" % amount,
                    {
                        'amount': amount,
                        'policy': self.generate_policy_for_authorities_amount(amount)
                    }
                ),
                [2, 4, 8, 16]
            ))
        super().__init__(cases)

    @staticmethod
    def generate_policy_for_authorities_amount(amount: int) -> str:
        """
        Generate a policy with a fixed size which uses attributes from the given amount of authorities.
        >>> len(set(AuthoritiesAmountExperiment.generate_policy_for_authorities_amount(2).split(' AND ')))
        16
        >>> len(set(AuthoritiesAmountExperiment.generate_policy_for_authorities_amount(4).split(' AND ')))
        16
        >>> len(set(AuthoritiesAmountExperiment.generate_policy_for_authorities_amount(8).split(' AND ')))
        16
        >>> len(set(AuthoritiesAmountExperiment.generate_policy_for_authorities_amount(16).split(' AND ')))
        16
        """
        # Nine attributes are used to make sure that there are no double attributes in the policy
        attribute_names = ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE']
        attributes = ['%s@AUTHORITY%d' % (attribute_names[i % len(attribute_names)], i % amount) for i in range(16)]
        return ' AND '.join(attributes)

    def setup(self):
        super().setup()
        # Set the read policy
        self.read_policy = self.state.case.arguments['policy']
        # Base amount of authorities on the current case
        self.attribute_authority_descriptions = list(map(
            lambda index: {
                'name': 'AUTHORITY%d' % index,
                'attributes': list(map(lambda a: a + ('@AUTHORITY%d' % index), [
                    'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE'
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

        # As each case has a different number of authorities, we clear the authority storage before each case.
        # Otherwise, the files containing the keys of non-present authorities would still exist.
        self.clear_attribute_authority_storage()
