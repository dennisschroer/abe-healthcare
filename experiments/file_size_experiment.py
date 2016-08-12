from os.path import join
from typing import List

from client.user_client import UserClient
from experiments.base_experiment import BaseExperiment, ExperimentCase
from service.insurance_service import InsuranceService
from shared.connection.base_connection import BaseConnection
from shared.connection.user_insurance_connection import UserInsuranceConnection
from shared.implementations.base_implementation import BaseImplementation
from shared.model.user import User
from shared.serializer.pickle_serializer import PickleSerializer
from shared.utils.random_file_generator import RandomFileGenerator


class FileSizeExperiment(BaseExperiment):
    attributes = ['TEST@TEST']
    policy = 'TEST@TEST'

    def __init__(self, cases: List[ExperimentCase] = None) -> None:
        super().__init__()
        self.client = None  # type: UserClient
        if cases is None:
            cases = list(map(lambda size: ExperimentCase(size, {'file_size': size}), [1, 2 ** 10, 2 ** 20, 2 ** 30]))
        self.cases = cases

        self.first_filename = None  # type:str
        self.update_filename = None  # type:str

    def global_setup(self):
        file_generator = RandomFileGenerator()
        input_path = self.get_experiment_input_path()
        for case in self.cases:
            file_generator.generate(case.arguments['file_size'], 2, input_path, skip_if_exists=True,
                                    verbose=True)

    def setup(self, implementation: BaseImplementation, case: ExperimentCase):
        super().setup(implementation, case)
        input_path = self.get_experiment_input_path()
        self.first_filename = join(input_path, '%i-0' % case.arguments['file_size'])
        self.update_filename = join(input_path, '%i-1' % case.arguments['file_size'])

        central_authority = self.implementation.create_central_authority()
        central_authority.setup()

        attribute_authority = self.implementation.create_attribute_authority('TEST')
        attribute_authority.setup(central_authority, self.attributes)

        serializer = PickleSerializer(self.implementation)

        insurance = InsuranceService(serializer, central_authority.global_parameters,
                                     self.implementation.create_public_key_scheme(),
                                     storage_path=self.get_insurance_storage_path())
        insurance.add_authority(attribute_authority)

        user = User('bob', self.implementation)
        connection = UserInsuranceConnection(insurance, serializer, benchmark=True)
        self.client = UserClient(user, connection, self.implementation,
                                 storage_path=self.get_user_client_storage_path())
        user.registration_data = central_authority.register_user(user.gid)
        user.issue_secret_keys(attribute_authority.keygen(user.gid, user.registration_data, self.attributes, 1))

    def run(self, case: ExperimentCase):
        location = self.client.encrypt_file(self.first_filename, self.policy, self.policy)
        with open(self.update_filename, 'rb') as update_file:
            self.client.update_file(location, update_file.read())
        self.client.update_policy_file(location, self.policy, self.policy)
        self.client.decrypt_file(location)

    def get_connections(self) -> List[BaseConnection]:
        return [self.client.insurance_connection]
