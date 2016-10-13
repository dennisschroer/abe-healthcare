import os
import pickle
from os import path
from os.path import join
from typing import Tuple, Any, List, Dict

from Crypto.PublicKey import RSA

from service.insurance_service import InsuranceService
from shared.connection.user_attribute_authority_connection import UserAttributeAuthorityConnection
from shared.connection.user_insurance_connection import UserInsuranceConnection
from shared.implementations.base_implementation import BaseImplementation
from shared.model.global_parameters import GlobalParameters
from shared.model.records.create_record import CreateRecord
from shared.model.records.data_record import DataRecord
from shared.model.records.policy_update_record import PolicyUpdateRecord
from shared.model.records.update_record import UpdateRecord
from shared.model.types import AbeEncryption, DecryptionKeys
from shared.model.user import User
from shared.utils.key_utils import extract_key_from_group_element

RSA_KEY_SIZE = 2048

USER_OWNER_KEY_FILENAME = '%s.der'
USER_REGISTRATION_DATA_FILENAME = '%s_registration.dat'
USER_SECRET_KEYS_FILENAME = '%s_secret_keys.dat'

DEFAULT_STORAGE_PATH = 'data/output'


class UserClient(object):
    def __init__(self, user: User,
                 implementation: BaseImplementation, verbose=False, storage_path=None, monitor_network=False) -> None:
        self.storage_path = DEFAULT_STORAGE_PATH if storage_path is None else storage_path
        self.user = user
        self.insurance = None  # type: InsuranceService
        self.implementation = implementation
        self.verbose = verbose
        self.monitor_network = monitor_network
        self._insurance_connection = None  # type: UserInsuranceConnection
        self._global_parameters = None  # type: GlobalParameters
        self._authority_connections = None  # type: Dict[str, UserAttributeAuthorityConnection]
        if not path.exists(self.storage_path):
            os.makedirs(self.storage_path)

    @property
    def global_parameters(self) -> GlobalParameters:
        """
        Gets the global parameters.
        :return: The global parameters
        """
        if self._global_parameters is None:
            self._global_parameters = self.insurance_connection.request_global_parameters()
        return self._global_parameters

    @property
    def authorities(self):
        return self.insurance_connection.request_authorities()

    @property
    def authority_connections(self) -> Dict[str, UserAttributeAuthorityConnection]:
        if self._authority_connections is None:
            self._authority_connections = {
                name: UserAttributeAuthorityConnection(authority, self.implementation.serializer,
                                                       benchmark=self.monitor_network, identifier=self.user.gid)
                for name, authority
                in self.authorities.items()
                }
        return self._authority_connections

    @property
    def insurance_connection(self) -> UserInsuranceConnection:
        if self._insurance_connection is None:
            self._insurance_connection = UserInsuranceConnection(self.insurance, self.implementation.serializer,
                                                                 benchmark=self.monitor_network,
                                                                 identifier=self.user.gid)
        return self._insurance_connection

    def reset_connections(self):
        self._insurance_connection = None
        self._authority_connections = None

    def authorities_public_keys(self, time_period):
        # Retrieve authority public keys
        return self.implementation.merge_public_keys(
            {
                name: authority.request_public_keys(time_period)
                for name, authority
                in self.authority_connections.items()
                }
        )

    def encrypt_file(self, filename: str, read_policy: str = None, write_policy: str = None,
                     time_period: int = 1) -> str:
        """
        Encrypt a file with the policies in the file with '.policy' appended. The policy file contains two lines.
        The first line is the read policy, the second line the write policy.
        :param filename: The filename (relative to /data/input) to encrypt
        :param read_policy: The read policy to use
        :param write_policy: The write policy to use
        :param time_period: The time period to use
        :return: The name of the encrypted data (in /data/storage/)
        """
        # if filename.endswith(".policy"):
        #     continue
        policy_filename = '%s.policy' % filename
        # Read input
        if self.verbose:
            print('Encrypting %s' % join('data/input', filename))
        if read_policy is None or write_policy is None:
            if self.verbose:
                print('           %s' % join('data/input', policy_filename))
            policy_file = open(join('data/input', policy_filename), 'r')
            read_policy = policy_file.readline()
            write_policy = policy_file.readline()

        file = open(join('data/input', filename), 'rb')
        # Encrypt a message
        create_record = self.create_record(read_policy, write_policy, file.read(), {'name': filename}, time_period)
        file.close()
        # Send to insurance (this also stores the record)
        return self.send_create_record(create_record)

    def create_record(self, read_policy: str, write_policy: str, message: bytes, info: dict,
                      time_period: int) -> CreateRecord:
        """
        Create a new record containing the encrypted message.
        :param time_period: The time period for which the record is encrypted
        :param read_policy: The read policy to encrypt with.
        :param write_policy: The write policy to encrypt with.
        :param message: The message to encrypt.
        :param info: Additional info to encrypt with the message.
        :return: records.create_record.CreateRecord The resulting record containing the encrypted message.
        """
        # Generate symmetric encryption key
        key, symmetric_key = self.implementation.generate_abe_key(self.global_parameters)

        # Generate key pairs for writers and data owner
        pke = self.implementation.public_key_scheme
        ske = self.implementation.symmetric_key_scheme
        write_key_pair = pke.generate_key_pair(RSA_KEY_SIZE)
        owner_key_pair = self.get_owner_key()

        # Encrypt data and create a record
        return CreateRecord(
            read_policy=read_policy,
            write_policy=write_policy,
            owner_public_key=owner_key_pair.publickey(),
            write_public_key=write_key_pair.publickey(),
            encryption_key_read=self.implementation.abe_encrypt(self.global_parameters,
                                                                self.authorities_public_keys(time_period), key,
                                                                read_policy, time_period),
            encryption_key_owner=pke.encrypt(symmetric_key, owner_key_pair),
            write_private_key=self.implementation.abe_encrypt_wrapped(self.global_parameters,
                                                                      self.authorities_public_keys(time_period),
                                                                      self.implementation.serializer.serialize_private_key(
                                                                          write_key_pair),
                                                                      write_policy,
                                                                      time_period),
            time_period=time_period,
            info=ske.ske_encrypt(pickle.dumps(info), symmetric_key),
            data=ske.ske_encrypt(message, symmetric_key)
        )

    def decrypt_file(self, location: str) -> str:
        """
        Decrypt the file with the given name (in /data/storage) and output it to /data/output
        :param location: The location of the file to decrypt (in /data/storage)
        :return: The name of the output file (in /data/output)
        """
        record = self.request_record(location)

        if self.verbose:
            print('Decrypting %s' % join('data/storage', location))

        info, data = self.decrypt_record(record)

        if self.verbose:
            print('Writing    %s' % join('data/output', info['name']))
        file = open(join(self.storage_path, info['name']), 'wb')
        file.write(data)
        file.close()
        return info['name']

    def _decryption_keys_for_read_key(self, record: DataRecord):
        return self.implementation.decryption_keys(self.global_parameters,
                                                   self.authority_connections,
                                                   self.user.secret_keys,
                                                   self.user.registration_data,
                                                   record.encryption_key_read,
                                                   record.time_period)

    def _decrypt_abe(self, ciphertext: AbeEncryption, decryption_keys: DecryptionKeys):
        """
        Decrypt the ABE ciphertext. The method calculates decryption keys if necessary.
        :param ciphertext: The ABE ciphertext to decrypt.
        :param decryption_keys: The decryption keys to use.
        :raise exceptions.policy_not_satisfied_exception.PolicyNotSatisfiedException
        :return: The plaintext
        """
        return self.implementation.abe_decrypt(self.global_parameters, decryption_keys, self.user.gid, ciphertext,
                                               self.user.registration_data)

    def decrypt_record(self, record: DataRecord) -> Tuple[dict, bytes]:
        """
        Decrypt a data record if possible.
        :param record: The data record to decrypt
        :raise exceptions.policy_not_satisfied_exception.PolicyNotSatisfiedException
        :return: info, data
        """
        ske = self.implementation.symmetric_key_scheme
        decryption_key = self._retrieve_decryption_key(record)
        return pickle.loads(ske.ske_decrypt(record.info, decryption_key)), ske.ske_decrypt(record.data, decryption_key)

    def _retrieve_decryption_key(self, record: DataRecord):
        """
        Retrieve the symmetric decryption key from the given date record, if possible.
        The key is retrieved by using the owner key if possible, otherwise ABE is used to retrieve the symmetric key.
        :param record: The DataRecord to retrieve the symmetric decryption key from.
        :return: The symmetric decryption key.
        :raise exceptions.policy_not_satisfied_exception.PolicyNotSatisfiedException
        """
        owner_keys = self.find_owner_keys(record.owner_public_key)
        if owner_keys is not None:
            pke = self.implementation.public_key_scheme
            decryption_key = pke.decrypt(record.encryption_key_owner, owner_keys)
        else:
            ske = self.implementation.symmetric_key_scheme
            # Check if we need to fetch update keys first
            abe_decryption_keys = self._decryption_keys_for_read_key(record)
            key = self._decrypt_abe(record.encryption_key_read, abe_decryption_keys)
            decryption_key = extract_key_from_group_element(self.global_parameters.group, key, ske.ske_key_size())
        return decryption_key

    def update_file(self, location: str, message: bytes = b'updated content'):
        """
        Decrypt the file with the given name (in /data/storage) and output it to /data/output
        :param location: The location of the file to decrypt (in /data/storage)
        :param message: The new message
        :return: The name of the output file (in /data/output)
        """
        # Give it to the user
        record = self.request_record(location)
        if self.verbose:
            print('Updating   %s' % join('data/storage', location))
        # Update the content
        update_record = self.update_record(record, message)
        # Send it to the insurance
        self.send_update_record(location, update_record)

    def update_record(self, record: DataRecord, message: bytes) -> UpdateRecord:
        """
        Update the content of a record
        :param record: The data record to update
        :param message: The new message
        :return: records.update_record.UpdateRecord An record containing the updated data
        """
        pke = self.implementation.public_key_scheme
        ske = self.implementation.symmetric_key_scheme
        # Retrieve the encryption key
        decryption_key = self._retrieve_decryption_key(record)
        # Retrieve the write secret key
        decryption_keys = self.implementation.decryption_keys(self.global_parameters,
                                                              self.authority_connections,
                                                              self.user.secret_keys,
                                                              self.user.registration_data,
                                                              record.write_private_key[0],
                                                              record.time_period)
        write_secret_key = RSA.importKey(
            self.implementation.abe_decrypt_wrapped(self.global_parameters, decryption_keys,
                                                    self.user.gid, record.write_private_key,
                                                    self.user.registration_data))
        # Encrypt the updated data
        data = ske.ske_encrypt(message, decryption_key)
        # Sign the data
        signature = pke.sign(write_secret_key, data)
        return UpdateRecord(data, signature)

    def update_policy_file(self, location: str, read_policy: str, write_policy: str, time_period: int = 1):
        record = self.request_record(location)
        if self.verbose:
            print('Policy update %s' % join('data/storage', location))
        # Update the content
        policy_update_record = self.update_policy(record, read_policy, write_policy, time_period)
        # Send it to the insurance
        self.send_policy_update_record(location, policy_update_record)

    def update_policy(self, record: DataRecord, read_policy: str, write_policy: str,
                      time_period: int) -> PolicyUpdateRecord:
        """
        Update the policies of a DataRecord
        :param record: The DataRecord to update the policies of
        :param read_policy: The new read policy
        :param write_policy: The new write_policy
        :param time_period: The new time period
        :return: A PolicyUpdateRecord containing the updated policies
        """
        pke = self.implementation.public_key_scheme
        ske = self.implementation.symmetric_key_scheme
        # Retrieve the encryption key
        decryption_key = self._retrieve_decryption_key(record)
        # Find the correct owner key
        owner_key_pair = self.find_owner_keys(record.owner_public_key)
        # Generate new encryption keys
        new_key, new_symmetric_key = self.implementation.generate_abe_key(self.global_parameters)
        # Generate new write keys
        write_key_pair = pke.generate_key_pair(RSA_KEY_SIZE)

        # Retrieve authority public keys
        authority_public_keys = self.authorities_public_keys(time_period)

        return PolicyUpdateRecord(
            read_policy=read_policy,
            write_policy=write_policy,
            write_public_key=write_key_pair.publickey(),
            encryption_key_read=self.implementation.abe_encrypt(self.global_parameters,
                                                                authority_public_keys, new_key, read_policy,
                                                                time_period),
            encryption_key_owner=pke.encrypt(new_symmetric_key, owner_key_pair),
            write_private_key=self.implementation.abe_encrypt_wrapped(self.global_parameters, authority_public_keys,
                                                                      write_key_pair.exportKey('DER'), write_policy,
                                                                      time_period),
            time_period=record.time_period,
            info=ske.ske_encrypt(ske.ske_decrypt(record.info, decryption_key),
                                 new_symmetric_key),
            data=ske.ske_encrypt(ske.ske_decrypt(record.data, decryption_key),
                                 new_symmetric_key),
            signature=pke.sign(owner_key_pair, pickle.dumps((read_policy, write_policy, time_period)))
        )

    def request_record(self, location: str) -> DataRecord:
        """
        Request the DataRecord on the given location from the insurance company.
        :param location: The location of the DataRecord to request
        :return: records.data_record.DataRecord the DataRecord, or None.
        """
        return self.insurance_connection.request_record(location)

    def request_secret_keys(self, authority_name: str, attributes: List[str], time_period: int) -> None:
        """
        Request secret keys from the authority with the given name for the given attributes, valid in the given
        time_period. The secret keys are stored on the user model. The authority only issues non-revoked attributes,
        so it is not guaranteed that the user has secret keys for all requested attributes after this method is invoked.
        After the request, the current secret keys are stored.
        :param authority_name: The name of the authority to request the secret keys from
        :param attributes: The attributes to request secret keys for
        :param time_period: The time period to request secret keys for, if applicable
        """
        connection = self.authority_connections[authority_name]
        secret_keys = connection.request_keygen(self.user.gid, self.user.registration_data, attributes, time_period)
        self.user.issue_secret_keys(secret_keys)

        self.save_user_secret_keys()

    def request_secret_keys_multiple_authorities(self, authority_attributes: Dict[str, List[str]],
                                                 time_period: int) -> None:
        """
        Request secret keys from multiple authorities for the given attributes, valid in the given
        time_period. The secret keys are stored on the user model. The authority only issues non-revoked attributes,
        so it is not guaranteed that the user has secret keys for all requested attributes after this method is invoked.
        After the requests, the current secret keys are stored.
        :param authority_attributes: A dictionary from the name of the authority to request the secret keys from to the
        list of attributes to request secret keys for from this authority.
        :param time_period: The time period to request secret keys for, if applicable
        """
        for authority_name, attributes in authority_attributes.items():  # type: ignore
            connection = self.authority_connections[authority_name]
            secret_keys = connection.request_keygen(self.user.gid, self.user.registration_data, attributes, time_period)
            self.user.issue_secret_keys(secret_keys)

        self.save_user_secret_keys()

    def save_user_secret_keys(self):
        save_file_path = os.path.join(self.storage_path, USER_SECRET_KEYS_FILENAME % self.user.gid)
        with open(save_file_path, 'wb') as f:
            f.write(self.implementation.serializer.serialize_user_secret_keys(self.user.secret_keys))

    def load_user_secret_keys(self):
        save_file_path = os.path.join(self.storage_path, USER_SECRET_KEYS_FILENAME % self.user.gid)
        with open(save_file_path, 'rb') as f:
            self.user.secret_keys = (self.implementation.serializer.deserialize_user_secret_keys(f.read()))

    def send_create_record(self, create_record: CreateRecord) -> str:
        """
        Send a CreateRecord to the insurance company.
        :param create_record: The CreateRecord to send.
        :type create_record: records.create_record.CreateRecord
        :return: The location of the created record.
        """
        return self.insurance_connection.send_create_record(create_record)

    def send_update_record(self, location: str, update_record: UpdateRecord) -> None:
        """
        Send an UpdateRecord to the insurance company.
        :param location: The location of the original record.
        :param update_record: The UpdateRecord to send.
        """
        self.insurance_connection.send_update_record(location, update_record)

    def send_policy_update_record(self, location: str, policy_update_record: PolicyUpdateRecord) -> None:
        """
        Send an PolicyUpdateRecord to the insurance company.
        :param location: The location of the original record.
        :param policy_update_record: The UpdateRecord to send.
        """
        self.insurance_connection.send_policy_update_record(location, policy_update_record)

    def register(self, insurance: InsuranceService):
        self.insurance = insurance
        registration_data = self.insurance_connection.send_register_user(self.user.gid)
        self.user.registration_data = registration_data
        self.save_registration_data()

    def save_registration_data(self):
        save_file_path = os.path.join(self.storage_path, USER_REGISTRATION_DATA_FILENAME % self.user.gid)
        if self.user.registration_data is None:
            if os.path.exists(save_file_path):
                os.remove(save_file_path)
        else:
            with open(save_file_path, 'wb') as f:
                f.write(self.implementation.serializer.serialize_registration_data(self.user.registration_data))

    def load_registration_data(self):
        save_file_path = os.path.join(self.storage_path, USER_REGISTRATION_DATA_FILENAME % self.user.gid)
        if path.exists(save_file_path):
            with open(save_file_path, 'rb') as f:
                self.user.registration_data = self.implementation.serializer.deserialize_registration_data(f.read())
        else:
            self.user.registration_data = None

    def get_owner_key(self) -> Any:
        """
        Loads the keys from storage, or creates them if they do not exist
        :return: The owner key pair
        """
        if self.user.owner_key_pair is None:
            try:
                self.user.owner_key_pair = self.load_owner_keys()
            except (IOError, FileNotFoundError):
                self.user.owner_key_pair = self.create_owner_key()
                self.save_owner_keys(self.user.owner_key_pair)
        return self.user.owner_key_pair

    def create_owner_key(self) -> Any:
        """
        Create a new key pair for this user, to be used for proving ownership.
        :return: A new key pair.

        >>> from shared.implementations.base_implementation import MockImplementation
        >>> user_client = UserClient(None, MockImplementation())
        >>> key_pair = user_client.create_owner_key()
        >>> key_pair is not None
        True
        """
        pke = self.implementation.public_key_scheme
        return pke.generate_key_pair(RSA_KEY_SIZE)

    def save_owner_keys(self, key_pair: Any) -> Any:
        """
        Save the given key pair.
        :param key_pair: The key pair to save.

        >>> from shared.implementations.base_implementation import MockImplementation
        >>> implementation = MockImplementation()
        >>> user = User('bob', implementation)
        >>> user_client = UserClient(user, implementation)
        >>> key_pair = user_client.create_owner_key()
        >>> user_client.save_owner_keys(key_pair)
        >>> os.path.exists(os.path.join(user_client.storage_path, USER_OWNER_KEY_FILENAME % user_client.user.gid))
        True
        """
        pke = self.implementation.public_key_scheme
        with open(os.path.join(self.storage_path, USER_OWNER_KEY_FILENAME % self.user.gid), 'wb') as f:
            f.write(pke.export_key(key_pair))

    def load_owner_keys(self) -> Any:
        """
        Load the owner key pair for this user.
        :return: The owner key pair.

        >>> from shared.implementations.base_implementation import MockImplementation
        >>> implementation = MockImplementation()
        >>> user = User('bob', implementation)
        >>> user_client = UserClient(user, implementation)
        >>> key_pair = user_client.create_owner_key()
        >>> user_client.save_owner_keys(key_pair)
        >>> loaded = user_client.load_owner_keys()
        >>> loaded == key_pair
        True
        """
        pke = self.implementation.public_key_scheme
        with open(os.path.join(self.storage_path, USER_OWNER_KEY_FILENAME % self.user.gid), 'rb') as f:
            key_pair = pke.import_key(f.read())
        return key_pair

    def find_owner_keys(self, public_key: Any) -> Any:
        """
        Find the owner keys belonging to the given public key
        :param public_key: The public key
        :return: The key pair beloning to the public key
        """
        # For now there is only one owner pair -> return that one
        key_pair = self.get_owner_key()
        if public_key == key_pair.publickey():
            return key_pair
        return None
