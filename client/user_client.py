import os
import pickle
from typing import Tuple, Any

from Crypto.PublicKey import RSA
from shared.model.global_parameters import GlobalParameters
from shared.model.records.create_record import CreateRecord
from shared.model.records.data_record import DataRecord
from shared.model.records.policy_update_record import PolicyUpdateRecord
from shared.model.types import AbeEncryption
from shared.model.user import User

from service.insurance_service import InsuranceService
from shared.implementations.base_implementation import BaseImplementation
from shared.model.records.update_record import UpdateRecord
from shared.utils.key_utils import extract_key_from_group_element

RSA_KEY_SIZE = 2048

DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
USER_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'users')
USER_OWNER_KEY_FILENAME = '%s.der'


class UserClient(object):
    def __init__(self, user: User, insurance_service: InsuranceService, implementation: BaseImplementation) -> None:
        self.user = user
        self.insurance_service = insurance_service
        self.implementation = implementation
        self._global_parameters = None  # type: GlobalParameters

    @property
    def global_parameters(self) -> GlobalParameters:
        """
        Gets the global parameters.
        :return: The global parameters
        """
        if self._global_parameters is None:
            self._global_parameters = self.insurance_service.global_parameters
        return self._global_parameters

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
        pke = self.implementation.create_public_key_scheme()
        ske = self.implementation.create_symmetric_key_scheme()
        write_key_pair = pke.generate_key_pair(RSA_KEY_SIZE)
        owner_key_pair = self.get_owner_key()

        # Retrieve authority public keys
        authority_public_keys = self.implementation.merge_public_keys(self.insurance_service.authorities, time_period)

        # Encrypt data and create a record
        return CreateRecord(
            read_policy=read_policy,
            write_policy=write_policy,
            owner_public_key=owner_key_pair.publickey(),
            write_public_key=write_key_pair.publickey(),
            encryption_key_read=self.implementation.abe_encrypt(self.global_parameters,
                                                                authority_public_keys, key, read_policy, time_period),
            encryption_key_owner=pke.encrypt(symmetric_key, owner_key_pair),
            write_private_key=self.implementation.abe_encrypt_wrapped(self.global_parameters, authority_public_keys,
                                                                      write_key_pair.exportKey('DER'), write_policy,
                                                                      time_period),
            time_period=time_period,
            info=ske.ske_encrypt(pickle.dumps(info), symmetric_key),
            data=ske.ske_encrypt(message, symmetric_key)
        )

    def _decrypt_abe(self, ciphertext: AbeEncryption, time_period: int):
        """
        Decrypt the ABE ciphertext. The method calculates decryption keys if necessary.
        :param ciphertext: The ABE ciphertext to decrypt.
        :param time_period: The time period.
        :raise exceptions.policy_not_satisfied_exception.PolicyNotSatisfiedException
        :return: The plaintext
        """
        decryption_keys = self.implementation.decryption_keys(self.global_parameters,
                                                              self.insurance_service.authorities,
                                                              self.user.secret_keys,
                                                              self.user.registration_data,
                                                              ciphertext,
                                                              time_period)
        return self.implementation.abe_decrypt(self.global_parameters, decryption_keys, self.user.gid, ciphertext,
                                               self.user.registration_data)

    def decrypt_record(self, record: DataRecord) -> Tuple[dict, bytes]:
        """
        Decrypt a data record if possible.
        :param record: The data record to decrypt
        :type record: records.data_record.DataRecord
        :raise exceptions.policy_not_satisfied_exception.PolicyNotSatisfiedException
        :return: info, data
        """
        ske = self.implementation.create_symmetric_key_scheme()
        # Check if we need to fetch update keys first
        key = self._decrypt_abe(record.encryption_key_read, record.time_period)
        symmetric_key = extract_key_from_group_element(self.global_parameters.group, key,
                                                       ske.ske_key_size())
        return pickle.loads(
            ske.ske_decrypt(record.info, symmetric_key)), ske.ske_decrypt(
            record.data,
            symmetric_key)

    def update_record(self, record: DataRecord, message: bytes) -> UpdateRecord:
        """
        Update the content of a record
        :param record: The data record to update
        :param message: The new message
        :return: records.update_record.UpdateRecord An record containing the updated data
        """
        pke = self.implementation.create_public_key_scheme()
        ske = self.implementation.create_symmetric_key_scheme()
        # Retrieve the encryption key
        key = self._decrypt_abe(record.encryption_key_read, record.time_period)
        symmetric_key = extract_key_from_group_element(self.global_parameters.group, key,
                                                       ske.ske_key_size())
        # Retrieve the write secret key
        decryption_keys = self.implementation.decryption_keys(self.global_parameters,
                                                              self.insurance_service.authorities,
                                                              self.user.secret_keys,
                                                              self.user.registration_data,
                                                              record.write_private_key[0],
                                                              record.time_period)
        write_secret_key = RSA.importKey(
            self.implementation.abe_decrypt_wrapped(self.global_parameters, decryption_keys,
                                                    self.user.gid, record.write_private_key,
                                                    self.user.registration_data))
        # Encrypt the updated data
        data = ske.ske_encrypt(message, symmetric_key)
        # Sign the data
        signature = pke.sign(write_secret_key, data)
        return UpdateRecord(data, signature)

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
        pke = self.implementation.create_public_key_scheme()
        ske = self.implementation.create_symmetric_key_scheme()
        # Retrieve the encryption key
        key = self._decrypt_abe(record.encryption_key_read, record.time_period)
        symmetric_key = extract_key_from_group_element(self.global_parameters.group, key,
                                                       ske.ske_key_size())
        # Find the correct owner key
        owner_key_pair = self.find_owner_keys(record.owner_public_key)
        # Generate new encryption keys
        new_key, new_symmetric_key = self.implementation.generate_abe_key(self.global_parameters)
        # Generate new write keys
        write_key_pair = pke.generate_key_pair(RSA_KEY_SIZE)

        # Retrieve authority public keys
        authority_public_keys = self.implementation.merge_public_keys(self.insurance_service.authorities, time_period)

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
            info=ske.ske_encrypt(ske.ske_decrypt(record.info, symmetric_key),
                                 new_symmetric_key),
            data=ske.ske_encrypt(ske.ske_decrypt(record.data, symmetric_key),
                                 new_symmetric_key),
            signature=pke.sign(owner_key_pair, pickle.dumps((read_policy, write_policy, time_period)))
        )

    def request_record(self, location: str) -> DataRecord:
        """
        Request the DataRecord on the given location from the insurance company.
        :param location: The location of the DataRecord to request
        :return: records.data_record.DataRecord the DataRecord, or None.
        """
        return self.insurance_service.load(location)

    def send_create_record(self, create_record: CreateRecord) -> str:
        """
        Send a CreateRecord to the insurance company.
        :param create_record: The CreateRecord to send.
        :type create_record: records.create_record.CreateRecord
        :return: The location of the created record.
        """
        return self.insurance_service.create(create_record)

    def send_update_record(self, location: str, update_record: UpdateRecord) -> None:
        """
        Send an UpdateRecord to the insurance company.
        :param location: The location of the original record.
        :param update_record: The UpdateRecord to send.
        """
        self.insurance_service.update(location, update_record)

    def send_policy_update_record(self, location: str, policy_update_record: PolicyUpdateRecord) -> None:
        """
        Send an PolicyUpdateRecord to the insurance company.
        :param location: The location of the original record.
        :param policy_update_record: The UpdateRecord to send.
        """
        self.insurance_service.policy_update(location, policy_update_record)

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
        >>> user_client = UserClient(None, None, MockImplementation())
        >>> key_pair = user_client.create_owner_key()
        >>> key_pair is not None
        True
        """
        pke = self.implementation.create_public_key_scheme()
        return pke.generate_key_pair(RSA_KEY_SIZE)

    def save_owner_keys(self, key_pair: Any) -> Any:
        """
        Save the given key pair.
        :param key_pair: The key pair to save.

        >>> from shared.implementations.base_implementation import MockImplementation
        >>> implementation = MockImplementation()
        >>> user = User('bob', implementation)
        >>> user_client = UserClient(user, None, implementation)
        >>> key_pair = user_client.create_owner_key()
        >>> user_client.save_owner_keys(key_pair)
        >>> os.path.exists(os.path.join(USER_PATH, USER_OWNER_KEY_FILENAME % user_client.user.gid))
        True
        """
        pke = self.implementation.create_public_key_scheme()
        if not os.path.exists(USER_PATH):
            os.makedirs(USER_PATH)
        with open(os.path.join(USER_PATH, USER_OWNER_KEY_FILENAME % self.user.gid), 'wb') as f:
            f.write(pke.export_key(key_pair))

    def load_owner_keys(self) -> Any:
        """
        Load the owner key pair for this user.
        :return: The owner key pair.

        >>> from shared.implementations.base_implementation import MockImplementation
        >>> implementation = MockImplementation()
        >>> user = User('bob', implementation)
        >>> user_client = UserClient(user, None, implementation)
        >>> key_pair = user_client.create_owner_key()
        >>> user_client.save_owner_keys(key_pair)
        >>> loaded = user_client.load_owner_keys()
        >>> loaded == key_pair
        True
        """
        pke = self.implementation.create_public_key_scheme()
        if not os.path.exists(USER_PATH):
            os.makedirs(USER_PATH)
        with open(os.path.join(USER_PATH, USER_OWNER_KEY_FILENAME % self.user.gid), 'rb') as f:
            key_pair = pke.import_key(f.read())
        return key_pair

    def find_owner_keys(self, public_key: Any) -> Any:
        """
        Find the owner keys belonging to the given public key
        :param public_key: The public key
        :return: The key pair beloning to the public key
        """
        # For now there is only one owner pair -> return that one
        return self.get_owner_key()
