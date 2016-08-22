import cProfile
import os
import shutil
from os.path import join
from typing import List, Dict, Any

from authority.attribute_authority import AttributeAuthority
from client.user_client import UserClient
from service.central_authority import CentralAuthority
from service.insurance_service import InsuranceService
from shared.connection.base_connection import BaseConnection
from shared.connection.user_insurance_connection import UserInsuranceConnection
from shared.implementations.base_implementation import BaseImplementation
from shared.model.user import User
from shared.serializer.pickle_serializer import PickleSerializer
from shared.utils.random_file_generator import RandomFileGenerator


class ExperimentCase(object):
    def __init__(self, name: str, arguments: Dict[str, Any]) -> None:
        self.name = name
        self.arguments = arguments


class BaseExperiment(object):
    # Default configurations
    attribute_authority_descriptions = [  # type: List[Dict[str, Any]]
        {
            'name': 'AUTHORITY1',
            'attributes': list(map(lambda a: a + '@AUTHORITY1', [
                'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN'
            ]))
        },
        {
            'name': 'AUTHORITY2',
            'attributes': list(map(lambda a: a + '@AUTHORITY2', [
                'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN'
            ]))
        }
    ]
    user_descriptions = [  # type: List[Dict[str, Any]]
        {
            'gid': 'USER1',
            'attributes': {
                'AUTHORITY1': ['ONE@AUTHORITY1', 'TWO@AUTHORITY1', 'THREE@AUTHORITY1', 'FOUR@AUTHORITY1'],
                'AUTHORITY2': ['SEVEN@AUTHORITY2', 'EIGHT@AUTHORITY2', 'NINE@AUTHORITY2', 'TEN@AUTHORITY2']
            }
        },
        {
            'gid': 'USER2',
            'attributes': {
                'AUTHORITY1': ['ONE@AUTHORITY1', 'TWO@AUTHORITY1', 'THREE@AUTHORITY1', 'FOUR@AUTHORITY1'],
                'AUTHORITY2': ['SEVEN@AUTHORITY2', 'EIGHT@AUTHORITY2', 'NINE@AUTHORITY2', 'TEN@AUTHORITY2']
            }
        },
    ]
    file_size = 10 * 1024 * 1024  # type: int
    read_policy = '(ONE@AUTHORITY1 AND SEVEN@AUTHORITY2) OR (TWO@AUTHORITY1 AND EIGHT@AUTHORITY2) OR (THREE@AUTHORITY1 AND NINE@AUTHORITY2)'
    write_policy = read_policy

    def __init__(self, cases: List[ExperimentCase] = None) -> None:
        self.memory_measure_interval = 0.05
        self.pr = cProfile.Profile()
        self.device_name = None  # type: str
        self.timestamp = None  # type: str
        self.file_name = None  # type: str

        self.central_authority = None  # type: CentralAuthority
        self.attribute_authorities = None  # type: List[AttributeAuthority]
        self.user_clients = None  # type: List[UserClient]

        if cases is None:
            cases = [ExperimentCase('base', None)]

        self.cases = cases  # type: List[ExperimentCase]
        self.current_case = None  # type: ExperimentCase
        self.current_implementation = None  # type:BaseImplementation
        self.serializer = None  # type: PickleSerializer

    def global_setup(self) -> None:
        """
        Setup all implementation and case independent things for this experiment, like generating random input files.
        This method is only called once for each experiment, namely at the very start.
        """
        file_generator = RandomFileGenerator()
        input_path = self.get_experiment_input_path()
        file_generator.generate(self.file_size, 1, input_path, skip_if_exists=True, verbose=True)

    def setup(self, implementation: BaseImplementation, case: ExperimentCase) -> None:
        """
        Setup all case dependant things for this experiment and this case.
        :return:
        """
        self.current_case = case
        self.current_implementation = implementation

        input_path = self.get_experiment_input_path()
        self.serializer = PickleSerializer(implementation)

        self.file_name = join(input_path, '%i-0' % self.file_size)

    def register_user_clients(self):
        """
        Register all current user clients in this experiment to the central authority.
        :return:
        """
        for user_client in self.user_clients:
            user_client.user.registration_data = self.central_authority.register_user(user_client.user.gid)

    def get_user_client(self, gid: str) -> UserClient:
        """
        Gets the UserClient for the given global identifier, or returns None.
        :param gid: The global identifier.
        :return: The user client or None.
        """
        return next((x for x in self.user_clients if x.user.gid == gid), None)

    def get_attribute_authority(self, name: str) -> AttributeAuthority:
        """
        Gets the AttributeAuthority for the given name, or returns None.
        :param name: The authority name.
        :return: The attribute authority or None.
        """
        return next((x for x in self.attribute_authorities if x.name == name), None)

    def generate_user_keys(self) -> None:
        """
        Generate the user secret keys for each current user client by generating the
        keys at the attribute authorities. The attributes to issue/generate are taken from the user
        descriptions (self.user_descriptions)
        :requires: self.user_clients is not None
        """
        for user_description in self.user_descriptions:
            user_client = self.get_user_client(user_description['gid'])  # type: ignore
            for authority_name, attributes in user_description['attributes'].items():  # type: ignore
                authority = self.get_attribute_authority(authority_name)
                user_client.user.issue_secret_keys(
                    authority.keygen(user_client.user.gid, user_client.user.registration_data, attributes, 1))

    def create_attribute_authorities(self, central_authority: CentralAuthority, implementation: BaseImplementation) -> \
            List[AttributeAuthority]:
        """
        Create the attribute authorities defined in the descriptions (self.attribute_authority_descriptions).
        :param central_authority: The central authority in the scheme.
        :param implementation: The implementation to use.
        :return: A list of attribute authorities.
        """
        return list(map(
            lambda d: self.create_attribute_authority(d, central_authority, implementation),
            self.attribute_authority_descriptions
        ))

    # noinspection PyMethodMayBeStatic
    def create_attribute_authority(self, authority_description: Dict[str, Any], central_authority: CentralAuthority,
                                   implementation: BaseImplementation) -> AttributeAuthority:
        """
        Create an attribute authority defined in a description.
        :param authority_description: The description of the authority.
        :param central_authority: The central authority in the scheme.
        :param implementation: The implementation to use.
        :return: The attribute authority.
        """
        attribute_authority = implementation.create_attribute_authority(authority_description['name'])
        attribute_authority.setup(central_authority, authority_description['attributes'])
        return attribute_authority

    def create_user_clients(self, implementation: BaseImplementation, insurance: InsuranceService) -> List[UserClient]:
        """
        Create the user clients defined in the descriptions (self.user_descriptions).
        :param implementation: The implementation to use.
        :param insurance: The insurance service to use.
        :return: A list of user clients.
        """
        return list(map(
            lambda d: self.create_user_client(d, insurance, implementation),
            self.user_descriptions
        ))

    def create_user_client(self, user_description: Dict[str, Any], insurance: InsuranceService,
                           implementation: BaseImplementation) -> UserClient:
        """
        Create a user client defined in the descriptions (self.user_descriptions).
        :param user_description: The description of the user.
        :param implementation: The implementation to use.
        :param insurance: The insurance service to use.
        :return: A list of user clients.
        """
        user = User(user_description['gid'], implementation)
        serializer = PickleSerializer(implementation)
        connection = UserInsuranceConnection(insurance, serializer, benchmark=True)
        client = UserClient(user, connection, implementation, storage_path=self.get_user_client_storage_path())
        return client

    def start_measurements(self) -> None:
        """
        Start the measurements. These are only part of the measurements, namely the one which need to run
        in the experiment process.
        :return:
        """
        self.pr.enable()

    def stop_measurements(self) -> None:
        """
        Stop the measurements.
        """
        self.pr.disable()

    def run(self):
        # Create central authority
        self.central_authority = self.current_implementation.create_central_authority()
        self.central_authority.setup()

        # Create insurance service
        insurance = InsuranceService(self.serializer, self.central_authority.global_parameters,
                                     self.current_implementation.create_public_key_scheme(),
                                     storage_path=self.get_insurance_storage_path())

        # Create attribute authorities
        self.attribute_authorities = self.create_attribute_authorities(self.central_authority,
                                                                       self.current_implementation)
        for authority in self.attribute_authorities:
            insurance.add_authority(authority)

        # Create user clients
        self.user_clients = self.create_user_clients(self.current_implementation, insurance)  # type: List[UserClient]
        self.register_user_clients()
        self.generate_user_keys()

        location = self.user_clients[0].encrypt_file(self.file_name, self.read_policy, self.write_policy)
        self.user_clients[1].decrypt_file(location)

    def get_connections(self) -> List[BaseConnection]:
        """
        Get all connections used in this experiment of which the usage should be outputted.
        :return: A list of connections
        """
        result = []  # type: List[BaseConnection]
        for user_client in self.user_clients:
            result += [user_client.insurance_connection]
        return result

    def get_name(self):
        return self.__class__.__name__

    def setup_directories(self) -> None:
        """
        Setup the directories used in this experiment. Empty directories and create them if they do not exist.
        """
        # Empty storage directories
        if os.path.exists(self.get_user_client_storage_path()):
            shutil.rmtree(self.get_user_client_storage_path())
        if os.path.exists(self.get_insurance_storage_path()):
            shutil.rmtree(self.get_insurance_storage_path())

        # Create directories
        if not os.path.exists(self.get_experiment_input_path()):
            os.makedirs(self.get_experiment_input_path())
        os.makedirs(self.get_user_client_storage_path())
        os.makedirs(self.get_insurance_storage_path())

    def get_experiment_storage_base_path(self) -> str:
        """
        Gets the base path of the location to be used for storage in this experiment.
        """
        return os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            '../data/experiments/%s' % self.get_name())

    def get_experiment_input_path(self) -> str:
        """
        Gets the path of the location to be used for the inputs of the experiment.
        """
        return os.path.join(self.get_experiment_storage_base_path(), 'input')

    def get_user_client_storage_path(self) -> str:
        """
        Gets the path of the location to be used for the storage of user client data.
        """
        return os.path.join(self.get_experiment_storage_base_path(), 'client')

    def get_insurance_storage_path(self) -> str:
        """
        Gets the path of the location to be used for the storage of the insurance service.
        """
        return os.path.join(self.get_experiment_storage_base_path(), 'insurance')
