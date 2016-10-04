import logging
import os
import shutil
from cProfile import Profile
from os import path
from os.path import join
from typing import List, Dict, Any, Callable

from memory_profiler import memory_usage
from psutil import Process

from authority.attribute_authority import AttributeAuthority
from client.user_client import UserClient
from experiments.enum.abe_step import ABEStep
from experiments.enum.implementations import implementations
from experiments.enum.measurement_type import MeasurementType
from experiments.experiment_case import ExperimentCase
from experiments.experiment_output import ExperimentOutput, OUTPUT_DETAILED
from experiments.experiment_state import ExperimentState
from service.central_authority import CentralAuthority
from service.insurance_service import InsuranceService
from shared.connection.base_connection import BaseConnection
from shared.implementations.base_implementation import BaseImplementation
from shared.model.user import User
from shared.utils.random_file_generator import RandomFileGenerator


class BaseExperiment(object):
    memory_measure_interval = 0.1
    """Indicates how often the memory should be measured, in seconds."""
    run_descriptions = {
        'setup_authsetup': 'always',
        'register_keygen': 'always'
    }
    """
    Description of which steps to run during the experiment. Steps can be run 'always', or only 'once'. In the latter,
    the step is run for each implementation once, prior to all experiments. This can be helpful if only the encryption
    and decryption is relevant.
    """
    attribute_authority_descriptions = [  # type: List[Dict[str, Any]]
        {
            'name': 'AUTHORITY0',
            'attributes': list(map(lambda a: a + '@AUTHORITY0', [
                'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN'
            ]))
        },
        {
            'name': 'AUTHORITY1',
            'attributes': list(map(lambda a: a + '@AUTHORITY1', [
                'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN'
            ]))
        }
    ]
    """
    Description of the attribute authorities to use in this experiment.
    Is a list of dicts, where each dict contains at least a name and a list of attributes.
    """
    user_descriptions = [  # type: List[Dict[str, Any]]
        {
            'gid': 'BOB',
            'attributes': {
                'AUTHORITY0': ['ONE@AUTHORITY0', 'TWO@AUTHORITY0', 'THREE@AUTHORITY0', 'FOUR@AUTHORITY0'],
                'AUTHORITY1': ['FIVE@AUTHORITY1', 'SIX@AUTHORITY1', 'SEVEN@AUTHORITY1', 'EIGHT@AUTHORITY1']
            }
        },
        {
            'gid': 'DOCTOR',
            'attributes': {
                'AUTHORITY0': attribute_authority_descriptions[0]['attributes'],
                'AUTHORITY1': attribute_authority_descriptions[1]['attributes']
            }
        },
    ]
    """Description of the users to use in this experiment."""
    generated_file_sizes = [10 * 1024 * 1024]  # type: List[int]
    """List of sizes of files to randomly generate as input files before the experiment."""
    encrypted_file_size = generated_file_sizes[0]
    """Size of the file to encrypt and decrypt."""
    read_policy = '(ONE@AUTHORITY0 AND SIX@AUTHORITY1)' \
                  ' OR (TWO@AUTHORITY0 AND SEVEN@AUTHORITY1)' \
                  ' OR (THREE@AUTHORITY0 AND EIGHT@AUTHORITY1)'
    """The read policy to use when encrypting."""
    write_policy = read_policy
    """The write policy to use when encrypting."""
    measurement_types = MeasurementType
    """The types of measurments to perform in this experiment."""
    implementations = implementations
    """The implementations to run this experiments on."""
    measurement_repeat = 100
    """The amount of times to repeat every measurement for each case and implementation."""

    def __init__(self, cases: List[ExperimentCase] = None) -> None:
        self.state = ExperimentState()  # type: ExperimentState
        self.output = ExperimentOutput(self.get_name(), self.state)  # type: ExperimentOutput
        """
        The current state of the experiment.
        This shows for example which implementation we currently use, and which measurements are performed.
        """

        # Experiment variables
        self.location = None  # type: str
        """Location of the encrypted data. Is set during the experiment"""
        self.memory_usages = None  # type: Dict[str, List[float]]
        self.cpu_times = None  # type: Dict[str, List[float]]
        self.profiler = None  # type: Profile
        self.psutil_process = None  # type: Process

        # Use case actors
        self.central_authority = None  # type: CentralAuthority
        self.attribute_authorities = None  # type: List[AttributeAuthority]
        self.user_clients = None  # type: List[UserClient]
        self.insurance = None  # type: InsuranceService

        # Experiment cases
        if cases is None:
            cases = [ExperimentCase('base', None)]
        self.cases = cases  # type: List[ExperimentCase]

    def global_setup(self) -> None:
        """
        Setup all things for this experiment independent of run, implementation and case,
        like generating random input files.
        This method is only called once for each experiment, namely at the very start.
        """
        self.generate_files()

    def generate_files(self) -> None:
        """Generate all input files as specified by the generated_file_sizes property."""
        file_generator = RandomFileGenerator()
        input_path = self.get_experiment_input_path()
        for size in self.generated_file_sizes:
            file_generator.generate(size, 1, input_path, skip_if_exists=True, verbose=True)

    @property
    def file_name(self) -> str:
        """File name of the file to encrypt. Is set during the experiment"""
        return join(self.get_experiment_input_path(), '%i-0' % self.encrypted_file_size)

    def setup(self) -> None:
        """
        Setup for a single run of this experiment for a single implementation, case and measurement type.
        """
        if OUTPUT_DETAILED and not path.exists(self.output.experiment_case_iteration_results_directory()):
            os.makedirs(self.output.experiment_case_iteration_results_directory())
        self.clear_insurance_storage()

    def tear_down(self) -> None:
        """
        Tear down after a single run of the experiment for a single implementation, case and measurement type.
        Note: this is run after the measurements are stopped, but before the measurements are finished.
        """
        if self.state.measurement_type == MeasurementType.storage_and_network:
            for authority in self.attribute_authorities:
                authority.save_attribute_keys()

    def reset_variables(self):
        self.location = None
        self.memory_usages = None
        self.cpu_times = None
        self.profiler = None
        self.psutil_process = None

        # Use case actors
        self.central_authority = None
        self.attribute_authorities = None
        self.user_clients = None
        self.insurance = None

    def setup_implementation_directories(self) -> None:
        """
        Setup the directories used in this experiment for a single implementation.
        Empties directories and create them if they do not exist.
        """
        assert self.state.implementation is not None

        # Empty storage directories
        if os.path.exists(self.get_user_client_storage_path()):
            shutil.rmtree(self.get_user_client_storage_path())

        # Create directories
        if not os.path.exists(self.get_experiment_input_path()):
            os.makedirs(self.get_experiment_input_path())
        os.makedirs(self.get_user_client_storage_path())

    def register_user_clients(self) -> None:
        """
        Register all current user clients in this experiment to the central authority.
        :return:
        """
        for user_client in self.user_clients:
            user_client.register()

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
        attribute_authority = implementation.create_attribute_authority(
            authority_description['name'],
            storage_path=self.get_attribute_authority_storage_path()
        )
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

    def _run_setup(self) -> None:
        # Create central authority
        self.central_authority = self.state.implementation.create_central_authority(
            storage_path=self.get_central_authority_storage_path())
        self.central_authority.central_setup()
        self.central_authority.save_global_parameters()
        self.setup_insurance()

    def setup_insurance(self) -> None:
        # Create insurance service
        self.insurance = InsuranceService(self.state.implementation.serializer,
                                          self.central_authority,
                                          self.state.implementation.public_key_scheme,
                                          storage_path=self.get_insurance_storage_path())

    def _run_authsetup(self) -> None:
        # Create attribute authorities
        self.attribute_authorities = self.create_attribute_authorities(self.central_authority,
                                                                       self.state.implementation)
        for authority in self.attribute_authorities:
            self.insurance.add_authority(authority)
            authority.save_attribute_keys()

    def _run_register(self) -> None:
        # Create user clients
        self.user_clients = self.create_user_clients(self.state.implementation,
                                                     self.insurance)  # type: List[UserClient]
        self.register_user_clients()

    def _run_keygen(self) -> None:
        """
        Generate the user secret keys for each current user client by generating the
        keys at the attribute authorities. The attributes to issue/generate are taken from the user
        descriptions (self.user_descriptions)
        :requires: self.user_clients is not None
        """
        for user_description in self.user_descriptions:
            user_client = self.get_user_client(user_description['gid'])  # type: ignore
            user_client.request_secret_keys_multiple_authorities(user_description['attributes'], 1)  # type: ignore
            user_client.save_user_secret_keys()

    def _run_encrypt(self) -> None:
        self.location = self.user_clients[0].encrypt_file(self.file_name, self.read_policy, self.write_policy)

    def _run_update_keys(self) -> None:
        for authority in self.attribute_authorities:
            authority.update_keys(1)

    def _run_decrypt(self) -> None:
        self.user_clients[1].decrypt_file(self.location)

    def run(self) -> None:
        self.global_setup()

        for implementation in self.implementations:
            self.state.implementation = implementation
            self.setup_implementation_directories()

            if self.run_descriptions['setup_authsetup'] == 'once':
                self._run_setup()
                self._run_authsetup()
            if self.run_descriptions['register_keygen'] == 'once':
                self._run_register()
                self._run_keygen()

            for i in range(0, self.measurement_repeat):
                for case in self.cases:
                    for measurement_type in self.measurement_types:  # type: ignore
                        self.state.iteration = i
                        self.state.case = case
                        self.state.measurement_type = measurement_type

                        self.log_current_state()
                        # noinspection PyBroadException
                        try:
                            self.setup()
                            self.start_measurements()

                            if self.run_descriptions['setup_authsetup'] == 'always':
                                self.run_step(ABEStep.setup, self._run_setup)
                                self.run_step(ABEStep.authsetup, self._run_authsetup)
                            if self.run_descriptions['register_keygen'] == 'always':
                                self.run_step(ABEStep.register, self._run_register)
                                self.run_step(ABEStep.keygen, self._run_keygen)
                            self.run_step(ABEStep.encrypt, self._run_encrypt)
                            self.run_step(ABEStep.update_keys, self._run_update_keys)
                            self.run_step(ABEStep.decrypt, self._run_decrypt)

                            self.stop_measurements()
                            self.tear_down()
                            self.finish_measurements()
                        except KeyboardInterrupt:
                            raise
                        except:
                            self.output.output_error()

            self.reset_variables()

    def run_step(self, abe_step: ABEStep, method: Callable[[], None]):
        if self.state.measurement_type == MeasurementType.memory:
            u = memory_usage((method, [], {}), interval=self.memory_measure_interval)
            self.memory_usages[abe_step.name] = [min(u), max(u), max(u) - min(u), len(u)]
        elif self.state.measurement_type == MeasurementType.cpu:
            times_before = self.psutil_process.cpu_times()
            method()
            times_after = self.psutil_process.cpu_times()
            self.cpu_times[abe_step.name] = (times_after.user - times_before.user) + \
                                            (times_after.system - times_before.system)
        else:
            method()

    def log_current_state(self) -> None:
        """
        Log the current state of the experiment, so the progress of the sequence can be followed.
        """
        logging.info("=> Running %s with implementation %s (%d/%d), iteration %d/%d, case %s, measurement %s" % (
            self.get_name(),
            self.state.implementation.get_name(),
            implementations.index(self.state.implementation) + 1,
            len(implementations),
            self.state.iteration + 1,
            self.measurement_repeat,
            self.state.case.name,
            str(self.state.measurement_type)
        ))

    def start_measurements(self) -> None:
        """
        Start the measurements for a single run.
        """
        logging.debug("Experiment.start")
        if self.state.measurement_type == MeasurementType.timings:
            self.profiler = Profile()
            self.profiler.enable()
        elif self.state.measurement_type == MeasurementType.cpu:
            self.cpu_times = dict()
            self.psutil_process = Process()
        elif self.state.measurement_type == MeasurementType.memory:
            self.memory_usages = dict()

    def stop_measurements(self) -> None:
        """
        Stop the measurements for the current run, but do not export the results yet.
        """
        if self.state.measurement_type == MeasurementType.timings:
            self.profiler.disable()

    def finish_measurements(self) -> None:
        """
        Finish the stopped measurements by exporting the results to the output files.
        """
        logging.debug("Experiment.finish")
        if self.state.measurement_type == MeasurementType.timings:
            self.output.output_timings(self.profiler)
        elif self.state.measurement_type == MeasurementType.memory:
            self.output.output_case_results('memory', self.memory_usages, variables=['min', 'max', 'diff', 'amount'])
        elif self.state.measurement_type == MeasurementType.storage_and_network:
            self.output.output_connections(self.get_connections())
            self.output.output_storage_space([
                {
                    'path': self.get_insurance_storage_path(),
                    'filename_mapper': lambda file: path.splitext(file)[1].strip('.')
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
        elif self.state.measurement_type == MeasurementType.cpu:
            self.output.output_cpu_times(self.cpu_times)

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

    def get_name(self) -> str:
        """
        Gets the name of this experiment.
        :return: The name of this experiment.
        """
        return self.__class__.__name__

    def clear_insurance_storage(self) -> None:
        """
        Clear the storage as used by the insurance company for the ciphertexts.
        """
        if os.path.exists(self.get_insurance_storage_path()):
            shutil.rmtree(self.get_insurance_storage_path())
        os.makedirs(self.get_insurance_storage_path())

    def clear_attribute_authority_storage(self) -> None:
        """
        Clear the storage as used by the insurance company for the ciphertexts.
        """
        if os.path.exists(self.get_attribute_authority_storage_path()):
            shutil.rmtree(self.get_attribute_authority_storage_path())
        os.makedirs(self.get_attribute_authority_storage_path())

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
            self.state.implementation.get_name(),
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
            self.state.implementation.get_name(),
            'authorities')

    def get_central_authority_storage_path(self) -> str:
        """
        Gets the path of the location to be used for the storage of the central authorities.
        """
        return os.path.join(
            self.get_experiment_storage_base_path(),
            self.state.implementation.get_name(),
            'central_authority')
