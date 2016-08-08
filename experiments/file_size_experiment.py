import os
from os.path import join
from typing import List

from client.user_client import UserClient
from experiments.base_experiment import BaseExperiment
from service.insurance_service import InsuranceService
from shared.connection.user_insurance_connection import UserInsuranceConnection
from shared.implementations.base_implementation import BaseImplementation
from shared.model.user import User
from shared.serializer.pickle_serializer import PickleSerializer
from shared.utils.random_file_generator import RandomFileGenerator


class FileSizeExperiment(BaseExperiment):
    data_location = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/experiments/FileSizeExperiment')

    attributes = ['TEST@TEST']
    policy = 'TEST@TEST'

    def __init__(self, implementation: BaseImplementation, sizes: List[int] = None) -> None:
        super().__init__()
        self.implementation = implementation
        self.client = None  # type: UserClient
        if sizes is None:
            sizes = [1, 2 ** 10, 2 ** 20]
        self.cases = sizes

    def setup(self):
        file_generator = RandomFileGenerator()
        for file_size in self.cases:
            file_generator.generate(file_size, 2, self.data_location, skip_if_exists=True)

        central_authority = self.implementation.create_central_authority()
        central_authority.setup()

        attribute_authority = self.implementation.create_attribute_authority('TEST')
        attribute_authority.setup(central_authority, self.attributes)

        insurance = InsuranceService(PickleSerializer(self.implementation), central_authority.global_parameters,
                                     self.implementation.create_public_key_scheme())
        insurance.add_authority(attribute_authority)

        user = User('bob', self.implementation)
        connection = UserInsuranceConnection(insurance)
        self.client = UserClient(user, connection, self.implementation)
        user.registration_data = central_authority.register_user(user.gid)
        user.issue_secret_keys(attribute_authority.keygen(user.gid, user.registration_data, self.attributes, 1))

    def run(self, case):
        first_filename = join(self.data_location, '%i-0' % case)
        update_filename = join(self.data_location, '%i-1' % case)

        location = self.client.encrypt_file(first_filename, self.policy, self.policy)
        with open(update_filename, 'rb') as update_file:
            self.client.update_file(location, update_file.read())
        self.client.update_policy_file(location, self.policy, self.policy)
        self.client.decrypt_file(location)


