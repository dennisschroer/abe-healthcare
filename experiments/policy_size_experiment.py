from os.path import join
from typing import List, Dict, Any

from client.user_client import UserClient
from experiments.base_experiment import BaseExperiment, ExperimentCase
from experiments_runner import debug
from service.central_authority import CentralAuthority
from service.insurance_service import InsuranceService
from shared.connection.base_connection import BaseConnection
from shared.connection.user_insurance_connection import UserInsuranceConnection
from shared.implementations.base_implementation import BaseImplementation
from shared.model.user import User
from shared.serializer.pickle_serializer import PickleSerializer
from shared.utils.random_file_generator import RandomFileGenerator


class PolicySizeExperiment(BaseExperiment):
    def __init__(self, cases: List[ExperimentCase] = None) -> None:
        super().__init__()
        if cases is None:
            attributes = list(map(lambda a: a + '@AUTHORITY1', [
                'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN'
            ]))
            cases = list(map(
                lambda size: ExperimentCase(str(size+1), {'policy': ' AND '.join(attributes[:size+1])}),
                range(10)
            ))
            if debug:
                for case in cases:
                    print(case.arguments)

        self.cases = cases

    def run(self):
        location = self.user_clients[0].encrypt_file(self.file_name, self.current_case.arguments['policy'], self.write_policy)
        self.user_clients[1].decrypt_file(location)
