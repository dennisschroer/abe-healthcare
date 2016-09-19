import logging
import os
import shutil
from cProfile import Profile
from multiprocessing import Condition, Event  # type: ignore
from os import path
from os.path import join
from typing import List, Dict, Any

from memory_profiler import memory_usage

from authority.attribute_authority import AttributeAuthority
from client.user_client import UserClient
from experiments.enum.measurement_type import MeasurementType
from experiments.experiment_case import ExperimentCase
from experiments.experiment_output import ExperimentOutput, OUTPUT_DETAILED
from experiments.experiment_state import ExperimentState, ExperimentProgress
from experiments.experiments_sequence_state import ExperimentsSequenceState
from service.central_authority import CentralAuthority
from service.insurance_service import InsuranceService
from shared.connection.base_connection import BaseConnection
from shared.implementations.base_implementation import BaseImplementation
from shared.model.user import User
from shared.utils.random_file_generator import RandomFileGenerator


class BaseExperiment(object):
    memory_measure_interval = 0.05
    run_descriptions = {
        # Can be 'always' or 'once'
        # When 'always', it is run in the run() method
        # When 'once', it is run during global setup and loaded in the run() method
        'setup_authsetup': 'always',
        'register_keygen': 'always',
        'encrypt_decrypt': 'always'
    }
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
                'AUTHORITY1': attribute_authority_descriptions[0]['attributes'],
                'AUTHORITY2': attribute_authority_descriptions[1]['attributes']
            }
        },
    ]
    file_size = 10 * 1024 * 1024  # type: int
    read_policy = '(ONE@AUTHORITY1 AND SEVEN@AUTHORITY2) OR (TWO@AUTHORITY1 AND EIGHT@AUTHORITY2) OR (THREE@AUTHORITY1 AND NINE@AUTHORITY2)'
    write_policy = read_policy

    def __init__(self, cases: List[ExperimentCase] = None) -> None:
        self.state = ExperimentState()  # type:ExperimentState
        self.output = None  # type: ExperimentOutput
        self._sequence_state = None  # type: ExperimentsSequenceState
        self.file_name = None  # type: str
        """File name of the file to encrypt. Is set during the experiment"""
        self.location = None  # type: str
        """Location of the encrypted data. Is set during the experiment"""

        self.central_authority = None  # type: CentralAuthority
        self.attribute_authorities = None  # type: List[AttributeAuthority]
        self.user_clients = None  # type: List[UserClient]

        if cases is None:
            cases = [ExperimentCase('base', None)]
        self.cases = cases  # type: List[ExperimentCase]

        # When the state of the next experiment is set
        self.state_sync = Condition()
        # - When the setup is done and the measurements should start
        self.setup_done_sync = Condition()
        # - When the results are saved and before the state is updated for the next experiment
        self.results_saved_sync = Condition()
        # Event used when the state changes to make the main thread do measurements at the start of each state
        self.state_change_event = Event()

        self.sync_count = 0
        self.memory_usages = None  # type: Dict[str, List[float]]
        self.profiler = None  # type: Profile

    @property
    def sequence_state(self):
        return self._sequence_state

    @sequence_state.setter
    def sequence_state(self, value: ExperimentsSequenceState):
        self._sequence_state = value
        self.output = ExperimentOutput(self.get_name(), self.state, self.sequence_state)

    def global_setup(self) -> None:
        """
        Setup all things for this experiment independent of run, implementation and case,
        like generating random input files.
        This method is only called once for each experiment, namely at the very start.
        """
        file_generator = RandomFileGenerator()
        input_path = self.get_experiment_input_path()
        file_generator.generate(self.file_size, 1, input_path, skip_if_exists=True, verbose=True)

    def setup(self) -> None:
        """
        Setup this experiment for a single implementation and a single case in a single run.
        """
        input_path = self.get_experiment_input_path()
        self.file_name = join(input_path, '%i-0' % self.file_size)

    def setup_directories(self) -> None:
        """
        Setup the directories used in this experiment. Empty directories and create them if they do not exist.
        """
        assert self.sequence_state.implementation is not None

        # Empty storage directories
        if os.path.exists(self.get_user_client_storage_path()):
            shutil.rmtree(self.get_user_client_storage_path())

        # Create directories
        if not os.path.exists(self.get_experiment_input_path()):
            os.makedirs(self.get_experiment_input_path())
        os.makedirs(self.get_user_client_storage_path())

    def register_user_clients(self):
        """
        Register all current user clients in this experiment to the central authority.
        :return:
        """
        for user_client in self.user_clients:
            user_client.set_registration_data(self.central_authority.register_user(user_client.user.gid))
            user_client.save_registration_data()

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

    def create_attribute_authority(self, authority_description: Dict[str, Any], central_authority: CentralAuthority,
                                   implementation: BaseImplementation) -> AttributeAuthority:
        """
        Create an attribute authority defined in a description.
        :param authority_description: The description of the authority.
        :param central_authority: The central authority in the scheme.
        :param implementation: The implementation to use.
        :return: The attribute authority.
        """
        attribute_authority = implementation.create_attribute_authority(authority_description['name'],
                                                                        storage_path=self.get_attribute_authority_storage_path())
        attribute_authority.setup(central_authority, authority_description['attributes'], 1)
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
        client = UserClient(user, insurance, implementation, storage_path=self.get_user_client_storage_path(),
                            monitor_network=self.state.measurement_type == MeasurementType.storage_and_network)
        return client

    def run_setup(self):
        self.set_progress(ExperimentProgress.setup)
        # Create central authority
        self.central_authority = self.sequence_state.implementation.create_central_authority(
            storage_path=self.get_central_authority_storage_path())
        self.central_authority.central_setup()
        self.central_authority.save_global_parameters()
        self.setup_insurance()

    def setup_insurance(self):
        # Create insurance service
        self.insurance = InsuranceService(self.sequence_state.implementation.serializer,
                                          self.central_authority.global_parameters,
                                          self.sequence_state.implementation.public_key_scheme,
                                          storage_path=self.get_insurance_storage_path())

    def run_authsetup(self):
        self.set_progress(ExperimentProgress.authsetup)
        # Create attribute authorities
        self.attribute_authorities = self.create_attribute_authorities(self.central_authority,
                                                                       self.sequence_state.implementation)
        for authority in self.attribute_authorities:
            self.insurance.add_authority(authority)
            authority.save_attribute_keys()

    def run_register(self):
        self.state.progress = ExperimentProgress.register
        # Create user clients
        self.user_clients = self.create_user_clients(self.sequence_state.implementation,
                                                     self.insurance)  # type: List[UserClient]
        self.register_user_clients()

    def run_keygen(self):
        """
        Generate the user secret keys for each current user client by generating the
        keys at the attribute authorities. The attributes to issue/generate are taken from the user
        descriptions (self.user_descriptions)
        :requires: self.user_clients is not None
        """
        self.set_progress(ExperimentProgress.keygen)
        for user_description in self.user_descriptions:
            user_client = self.get_user_client(user_description['gid'])  # type: ignore
            user_client.request_secret_keys_multiple_authorities(user_description['attributes'], 1)  # type: ignore
            user_client.save_user_secret_keys()

    def run_encrypt(self):
        self.set_progress(ExperimentProgress.encrypt)
        self.location = self.user_clients[0].encrypt_file(self.file_name, self.read_policy, self.write_policy)

    def run_decrypt(self):
        self.set_progress(ExperimentProgress.decrypt)
        self.user_clients[1].decrypt_file(self.location)

    def run(self):
        self.state.progress = ExperimentProgress.experiment_setup

        self.setup()

        if self.run_descriptions['setup_authsetup'] == 'once':
            self.run_setup()
            self.run_authsetup()
        if self.run_descriptions['register_keygen'] == 'once':
            self.run_register()
            self.run_keygen()

        for case in self.cases:
            self.state.case = case
            for measurement_type in MeasurementType:  # type: ignore
                try:
                    self.state.measurement_type = measurement_type

                    self.sync(self.state_sync)  # 1

                    if OUTPUT_DETAILED and not path.exists(self.output.experiment_case_iteration_results_directory()):
                        os.makedirs(self.output.experiment_case_iteration_results_directory())
                    self.clear_insurance_storage()

                    self.start_measurements()  # 2

                    if self.state.measurement_type == MeasurementType.memory:
                        if self.run_descriptions['setup_authsetup'] == 'always':
                            u = memory_usage((self.run_setup, [], {}), interval=self.memory_measure_interval)
                            self.memory_usages['setup'] = [min(u), max(u), len(u)]
                            u = memory_usage((self.run_authsetup, [], {}), interval=self.memory_measure_interval)
                            self.memory_usages['authsetup'] = [min(u), max(u), len(u)]
                        if self.run_descriptions['register_keygen'] == 'always':
                            u = memory_usage((self.run_register, [], {}), interval=self.memory_measure_interval)
                            self.memory_usages['register'] = [min(u), max(u), len(u)]
                            u = memory_usage((self.run_keygen, [], {}), interval=self.memory_measure_interval)
                            self.memory_usages['keygen'] = [min(u), max(u), len(u)]

                        u = memory_usage((self.run_encrypt, [], {}), interval=self.memory_measure_interval)
                        self.memory_usages['encrypt'] = [min(u), max(u), len(u)]
                        u = memory_usage((self.run_decrypt, [], {}), interval=self.memory_measure_interval)
                        self.memory_usages['decrypt'] = [min(u), max(u), len(u)]
                    else:
                        if self.run_descriptions['setup_authsetup'] == 'always':
                            self.run_setup()
                            self.run_authsetup()
                        if self.run_descriptions['register_keygen'] == 'always':
                            self.run_register()
                            self.run_keygen()
                        self.run_encrypt()
                        self.run_decrypt()

                    self.stop_measurements()

                    if measurement_type == MeasurementType.storage_and_network:
                        for authority in self.attribute_authorities:
                            authority.save_attribute_keys()

                    self.finish_measurements()  # 0
                except:
                    self.output.output_error()
                    self.state.progress = ExperimentProgress.experiment_setup
                    self.remaining_syncs()

        self.state.progress = ExperimentProgress.stopping
        self.sync(self.state_sync)

    def start_measurements(self):
        logging.debug("Experiment.start")
        if self.state.measurement_type == MeasurementType.timings:
            self.profiler = Profile()
            self.profiler.enable()
        self.memory_usages = dict()

        self.state.progress = ExperimentProgress.experiment_starting
        self.sync(self.setup_done_sync)
        # self.setup_lock.acquire()
        # self.setup_lock.notify()
        # self.setup_lock.release()

    def stop_measurements(self):
        logging.debug("Experiment.stop")
        self.state.progress = ExperimentProgress.experiment_setup
        if self.state.measurement_type == MeasurementType.timings:
            self.profiler.disable()

    def finish_measurements(self):
        logging.debug("Experiment.finish")
        if self.state.measurement_type == MeasurementType.timings:
            self.output.output_timings(self.profiler)
        if self.state.measurement_type == MeasurementType.memory:
            self.output.output_case_results('memory', self.memory_usages, variables=['min', 'max', 'amount'])
        if self.state.measurement_type == MeasurementType.storage_and_network:
            self.output.output_connections(self.get_connections())
            self.output.output_storage_space([
                {
                    'path': self.get_insurance_storage_path(),
                    'filename_mapper': lambda file: path.splitext(file)[1]
                },
                {
                    'path': self.get_user_client_storage_path()
                },
                {
                    'path': self.get_attribute_authority_storage_path()
                },
                {
                    'path': self.get_central_authority_storage_path()
                }
            ])
        self.sync(self.results_saved_sync)
        # Now sync with the other process

    def set_progress(self, value: ExperimentProgress):
        self.state.progress = value

    def sync(self, condition):
        """
        Synchronize with the main process. This happens at three moments:
        - When the state of the next experiment is set
        - When the setup is done and the measurements should start
        - When the results are saved and before the state is updated for the next experiment
        """
        with condition:
            condition.notify_all()
            logging.debug("Experiment.sync %s", condition)
            self.sync_count = (self.sync_count + 1) % 3

    def remaining_syncs(self):
        if self.sync_count == 1:
            self.sync(self.setup_done_sync)
            self.sync(self.results_saved_sync)
        elif self.sync_count == 2:
            self.sync(self.results_saved_sync)

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

    def get_connections(self) -> List[BaseConnection]:
        """
        Get all connections used in this experiment of which the usage should be outputted.
        :return: A list of connections
        """
        result = []  # type: List[BaseConnection]
        for user_client in self.user_clients:
            result += [user_client.insurance_connection]
            result += user_client.authority_connections.values()
        return result

    def get_name(self):
        return self.__class__.__name__

    def clear_insurance_storage(self) -> None:
        if os.path.exists(self.get_insurance_storage_path()):
            shutil.rmtree(self.get_insurance_storage_path())
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
        return os.path.join(
            self.get_experiment_storage_base_path(),
            self.sequence_state.implementation.get_name(),
            'client')

    def get_insurance_storage_path(self) -> str:
        """
        Gets the path of the location to be used for the storage of the insurance service.
        """
        return os.path.join(
            self.get_experiment_storage_base_path(),
            'insurance')

    def get_attribute_authority_storage_path(self) -> str:
        """
        Gets the path of the location to be used for the storage of the attribute authorities.
        """
        return os.path.join(
            self.get_experiment_storage_base_path(),
            self.sequence_state.implementation.get_name(),
            'authorities')

    def get_central_authority_storage_path(self) -> str:
        """
        Gets the path of the location to be used for the storage of the central authorities.
        """
        return os.path.join(
            self.get_experiment_storage_base_path(),
            self.sequence_state.implementation.get_name(),
            'central_authority')
