from implementations.base_implementation import BaseImplementation
from records.create_record import CreateRecord
from records.update_record import UpdateRecord
from utils.key_utils import extract_key_from_group_element
from Crypto.PublicKey import RSA
import os
import pickle

RSA_KEY_SIZE = 2048


class User(object):
    def __init__(self, gid, insurance_service, implementation):
        """
        Create a new user
        :param gid: The global identifier of this user
        :param insurance_service: The insurance service
        :type insurance_service: scheme.insurance_service.InsuranceService
        :param implementation:
        :type implementation: implementations.base_implementation.BaseImplementation
        """
        self.gid = gid
        self.insurance_service = insurance_service
        self.implementation = implementation
        self.secret_keys = implementation.setup_secret_keys(self)
        self._owner_key_pair = None
        self._global_parameters = None

    def issue_secret_keys(self, secret_keys):
        """
        Issue new secret keys to this user.
        :param secret_keys:
        :type secret_keys: dict

        >>> dummyImplementation = MockImplementation()
        >>> user = User("bob", None, dummyImplementation)
        >>> user.secret_keys
        {}
        >>> user.issue_secret_keys({'a': {'foo': 'bar'}})
        >>> user.secret_keys == {'a': {'foo': 'bar'}}
        True
        >>> user.issue_secret_keys({'b': {'bla': 'bla'}})
        >>> user.secret_keys == {'a': {'foo': 'bar'}, 'b': {'bla': 'bla'}}
        True
        """
        self.implementation.update_secret_keys(self.secret_keys, secret_keys)
        self.secret_keys.update(secret_keys)

    @property
    def global_parameters(self):
        """
        Gets the global parameters.
        :return: The global parameters
        """
        if self._global_parameters is None:
            self._global_parameters = self.insurance_service.global_parameters
        return self._global_parameters

    @property
    def owner_key_pair(self):
        """
        Loads the keys from storage, or creates them if they do not exist
        :return: The owner key pair
        """
        if self._owner_key_pair is None:
            try:
                self._owner_key_pair = self.load_owner_keys()
            except IOError:
                self._owner_key_pair = self.create_owner_key_pair()
                self.save_owner_keys(self._owner_key_pair)
        return self._owner_key_pair

    def create_owner_key_pair(self):
        """
        Create a new key pair for this user, to be used for proving ownership.
        :return: A new key pair.

        >>> user = User("bob", None, MockImplementation())
        >>> key_pair = user.create_owner_key_pair()
        >>> key_pair is not None
        True
        """
        return self.implementation.pke_generate_key_pair(RSA_KEY_SIZE)

    def create_record(self, read_policy, write_policy, message, info):
        """
        Create a new record containing the encrypted message.
        :param read_policy: The read policy to encrypt with.
        :param write_policy: The write policy to encrypt with.
        :param message: The message to encrypt.
        :param info: Additional info to encrypt with the message.
        :return: records.create_record.CreateRecord The resulting record containing the encrypted message.
        """
        # Generate symmetric encryption key
        key, symmetric_key = self.implementation.generate_abe_key(self.global_parameters)

        # Generate key pairs for writers and data owner
        write_key_pair = self.implementation.pke_generate_key_pair(RSA_KEY_SIZE)
        owner_key_pair = self.owner_key_pair

        self.save_owner_keys(owner_key_pair)

        # Retrieve authority public keys
        authority_public_keys = self.insurance_service.merge_public_keys()

        # Encrypt data and create a record
        return CreateRecord(
            read_policy=read_policy,
            write_policy=write_policy,
            owner_public_key=owner_key_pair.publickey(),
            write_public_key=write_key_pair.publickey(),
            encryption_key_read=self.implementation.abe_encrypt(self.global_parameters,
                                                                authority_public_keys, key, read_policy),
            encryption_key_owner=self.implementation.pke_encrypt(symmetric_key, owner_key_pair),
            write_private_key=self.implementation.abe_encrypt_wrapped(self.global_parameters, authority_public_keys,
                                                                      write_key_pair.exportKey('DER'), write_policy),
            info=self.implementation.ske_encrypt(pickle.dumps(info), symmetric_key),
            data=self.implementation.ske_encrypt(message, symmetric_key)
        )

    def save_owner_keys(self, key_pair):
        """
        Save the given key pair.
        :param key_pair: The key pair to save.

        >>> user = User("bob", None, MockImplementation())
        >>> key_pair = user.create_owner_key_pair()
        >>> user.save_owner_keys(key_pair)
        >>> os.path.exists('data/users/%s/owner.der' % user.gid)
        True
        """
        if not os.path.exists('data/users/%s' % self.gid):
            os.makedirs('data/users/%s' % self.gid)
        with open('data/users/%s/owner.der' % self.gid, 'wb') as f:
            f.write(key_pair.exportKey('DER'))

    def load_owner_keys(self):
        """
        Load the owner key pair for this user.
        :return: The owner key pair.

        >>> user = User("bob", None, MockImplementation())
        >>> key_pair = user.create_owner_key_pair()
        >>> user.save_owner_keys(key_pair)
        >>> loaded = user.load_owner_keys()
        >>> loaded == key_pair
        True
        """
        with open('data/users/%s/owner.der' % self.gid, 'rb') as f:
            key_pair = RSA.importKey(f.read())
        return key_pair

    def send_create_record(self, create_record):
        """
        Send a CreateRecord to the insurance company.
        :param create_record: The CreateRecord to send.
        :type create_record: records.create_record.CreateRecord
        :return: The location of the created record.
        """
        return self.insurance_service.create(create_record)

    def request_record(self, location):
        """
        Request the DataRecord on the given location from the insurance company.
        :param location: The location of the DataRecord to request
        :return: records.data_record.DataRecord the DataRecord, or None.
        """
        return self.insurance_service.load(location)

    def decrypt_record(self, record):
        """
        Decrypt a data record if possible.
        :param record: The data record to decrypt
        :type record: records.data_record.DataRecord
        :return: info, data
        """
        key = self.implementation.abe_decrypt(self.global_parameters, self.secret_keys,
                                              record.encryption_key_read)
        symmetric_key = extract_key_from_group_element(self.global_parameters.group, key,
                                                       self.implementation.ske_key_size())
        return pickle.loads(
            self.implementation.ske_decrypt(record.info, symmetric_key)), self.implementation.ske_decrypt(record.data,
                                                                                                          symmetric_key)


class MockImplementation(BaseImplementation):
    """
    Mock implementation for testing purposes
    """

    def update_secret_keys(self, base, secret_keys):
        base.update(secret_keys)

    def setup_secret_keys(self, user):
        return {}
