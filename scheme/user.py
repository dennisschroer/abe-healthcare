from records.create_record import CreateRecord
from charm.core.math.pairing import GT
from utils.key_utils import extract_key_from_group_element, create_key_pair
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA

RSA_KEY_SIZE = 2048


class User(object):
    def __init__(self, gid, insurance_service, abe_encryption, abe_decryption):
        """
        Create a new user
        :param gid: The global identifier of this user
        :param insurance_service: The insurance service
        :type insurance_service: scheme.insurance_service.InsuranceService
        :param abe_encryption:
        :param abe_decryption:
        """
        self.gid = gid
        self.insurance_service = insurance_service
        self.abe_encryption = abe_encryption
        self.abe_decryption = abe_decryption
        self.secret_keys = {}
        self.owner_key_pairs = []
        self._global_parameters = None

    def issue_secret_keys(self, secret_keys):
        """
        Issue new secret keys to this user.
        :param secret_keys:
        :type secret_keys: dict

        >>> user = User("bob", None, None, None)
        >>> user.secret_keys
        {}
        >>> user.issue_secret_keys({'a': {'foo': 'bar'}})
        >>> user.secret_keys == {'a': {'foo': 'bar'}}
        True
        >>> user.issue_secret_keys({'b': {'bla': 'bla'}})
        >>> user.secret_keys == {'a': {'foo': 'bar'}, 'b': {'bla': 'bla'}}
        True
        """
        self.secret_keys.update(secret_keys)

    @property
    def global_parameters(self):
        if self._global_parameters is None:
            self._global_parameters = self.insurance_service.global_parameters
        return self._global_parameters

    def create_owner_key_pair(self):
        key_pair = create_key_pair(RSA_KEY_SIZE)
        self.owner_key_pairs.append(key_pair)
        return key_pair

    def create_record(self, read_policy, write_policy, message):
        # Generate symmetric encryption key
        key = self.global_parameters.group.random(GT)
        symmetric_key = extract_key_from_group_element(self.global_parameters.group, key, 32)

        # Generate key pairs for writers and data owner
        write_key_pair = create_key_pair(RSA_KEY_SIZE)
        owner_key_pair = self.create_owner_key_pair()

        # Setup encryption
        symmetric_encryption = AES.new(symmetric_key, AES.MODE_CBC, 'This is an IV456')
        owner_assymmetric_encryption = PKCS1_OAEP.new(owner_key_pair)

        # Retrieve authority public keys
        authority_public_keys = self.insurance_service.merge_public_keys()

        # Encrypt data and create a record
        return CreateRecord(
            read_policy=read_policy,
            write_policy=write_policy,
            owner_public_key=owner_key_pair.publickey(),
            write_public_key=write_key_pair.publickey(),
            encryption_key_read=self.abe_encryption(self.global_parameters.scheme_parameters, authority_public_keys, key, read_policy),
            encryption_key_owner=owner_assymmetric_encryption.encrypt(symmetric_key),
            write_private_key=None,
            # write_private_key=self.abe_encryption(authority_public_keys, self.global_parameters.scheme_parameters, write_key_pair, write_policy),
            data=symmetric_encryption.encrypt(message)
        )
