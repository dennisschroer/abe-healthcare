import cProfile
import os
import shutil
from typing import List, Dict, Any

from client.user_client import UserClient
from service.central_authority import CentralAuthority
from service.insurance_service import InsuranceService
from shared.connection.base_connection import BaseConnection
from shared.connection.user_insurance_connection import UserInsuranceConnection
from shared.implementations.base_implementation import BaseImplementation
from shared.model.user import User
from shared.serializer.pickle_serializer import PickleSerializer


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
    user_descriptions = [
        {
            'gid': 'USER1',
            'attributes': ['ONE@AUTHORITY1', 'TWO@AUTHORITY1', 'THREE@AUTHORITY1', 'FOUR@AUTHORITY1',
                           'SEVEN@AUTHORITY2', 'EIGHT@AUTHORITY2', 'NINE@AUTHORITY2', 'TEN@AUTHORITY2']
        },
        {
            'gid': 'USER2',
            'attributes': ['ONE@AUTHORITY1', 'TWO@AUTHORITY1', 'THREE@AUTHORITY1', 'FOUR@AUTHORITY1',
                           'SEVEN@AUTHORITY2', 'EIGHT@AUTHORITY2', 'NINE@AUTHORITY2', 'TEN@AUTHORITY2']
        },
    ]
    file_sizes = [10 * 1024 * 1024]  # type: List[int]
    read_policy = '(ONE@AUTHORITY1 AND SEVEN@AUTHORITY2) OR (TWO@AUTHORITY1 AND EIGHT@AUTHORITY2) OR (THREE@AUTHORITY1 AND NINE@AUTHORITY2)'
    write_policy = read_policy

    def __init__(self) -> None:
        self.memory_measure_interval = 0.05
        self.pr = cProfile.Profile()
        self.cases = list()  # type: List[ExperimentCase]
        self.device_name = None  # type: str
        self.timestamp = None  # type: str

    def global_setup(self) -> None:
        """
        Setup all implementation and case independent things for this experiment, like generating random input files.
        This method is only called once for each experiment, namely at the very start.
        """
        raise NotImplementedError()

    def setup(self, implementation: BaseImplementation, case: ExperimentCase):
        """
        Setup all case dependant things for this experiment.
        :return:
        """
        raise NotImplementedError()

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

    def run(self, case: ExperimentCase) -> None:
        raise NotImplementedError()

    def get_connections(self) -> List[BaseConnection]:
        """
        Get all connections used in this experiment of which the usage should be outputted.
        :return: A list of connections
        """
        raise NotImplementedError()

    def get_name(self):
        return self.__class__.__name__

    def create_attribute_authorities(self, central_authority: CentralAuthority, implementation: BaseImplementation):
        return list(map(
            lambda d: self.create_attribute_authority(d, central_authority, implementation),
            self.attribute_authority_descriptions
        ))

    # noinspection PyMethodMayBeStatic
    def create_attribute_authority(self, authority_description: Dict[str, Any], central_authority: CentralAuthority,
                                   implementation: BaseImplementation):
        attribute_authority = implementation.create_attribute_authority(authority_description['name'])
        attribute_authority.setup(central_authority, authority_description['attributes'])
        return attribute_authority

    def create_user_clients(self, implementation: BaseImplementation, insurance: InsuranceService):
        return list(map(
            lambda d: self.create_user_client(d, insurance, implementation),
            self.user_descriptions
        ))

    def create_user_client(self, user_description: Dict[str, Any], insurance: InsuranceService, implementation: BaseImplementation):
        user = User(user_description['gid'], implementation)
        serializer = PickleSerializer(implementation)
        connection = UserInsuranceConnection(insurance, serializer, benchmark=True)
        client = UserClient(user, connection, implementation, storage_path=self.get_user_client_storage_path())
        return client

    def setup_directories(self):
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

    def get_experiment_storage_base_path(self):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            '../data/experiments/%s' % self.get_name())

    def get_experiment_input_path(self):
        return os.path.join(self.get_experiment_storage_base_path(), 'input')

    def get_user_client_storage_path(self):
        return os.path.join(self.get_experiment_storage_base_path(), 'client')

    def get_insurance_storage_path(self):
        return os.path.join(self.get_experiment_storage_base_path(), 'insurance')
