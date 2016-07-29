import os

from os.path import join

from client.user_client import UserClient
from service.insurance_service import InsuranceService
from shared.connection.user_insurance_connection import UserInsuranceConnection
from shared.implementations.base_implementation import BaseImplementation
from shared.model.user import User
from shared.serializer.pickle_serializer import PickleSerializer
from shared.utils.random_file_generator import RandomFileGenerator


class FileSizeExperiment(object):
    data_location = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data/file_size_experiment')

    attributes = ['TEST@TEST']
    policy = 'TEST@TEST'

    def __init__(self, implementation: BaseImplementation, sizes=None):
        self.implementation = implementation
        if sizes is None:
            sizes = [1, 2 ** 10, 2 ** 20, 2 ** 30]
        self.sizes = sizes

    def setup(self):
        file_generator = RandomFileGenerator()
        for file_size in self.sizes:
            file_generator.generate(file_size, 2, self.data_location, skip_if_exists=True)

    def run(self):
        central_authority = self.implementation.create_central_authority()
        central_authority.setup()

        attribute_authority = self.implementation.create_attribute_authority('TEST')
        attribute_authority.setup(central_authority, self.attributes)

        insurance = InsuranceService(PickleSerializer(self.implementation), central_authority.global_parameters,
                                     self.implementation.create_public_key_scheme())
        insurance.add_authority(attribute_authority)

        user = User('bob', self.implementation)
        connection = UserInsuranceConnection(insurance)
        client = UserClient(user, connection, self.implementation)
        user.registration_data = central_authority.register_user(user.gid)
        user.issue_secret_keys(attribute_authority.keygen(user.gid, user.registration_data, self.attributes, 1))

        for file_size in self.sizes:
            first_filename = join(self.data_location, '%i-0' % file_size)
            update_filename = join(self.data_location, '%i-1' % file_size)

            location = client.encrypt_file(first_filename, self.policy, self.policy)
            with open(update_filename, 'rb') as update_file:
                client.update_file(location, update_file.read())
            client.update_policy_file(location, self.policy, self.policy)
            client.decrypt_file(location)


if __name__ == '__main__':
    experiment = FileSizeExperiment()
    experiment.setup()
    experiment.run()
