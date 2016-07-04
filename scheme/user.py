from records.create_record import CreateRecord
from charm.core.math.pairing import GT
from utils.key_utils import extract_key_from_group_element, create_key_pair
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA

RSA_KEY_SIZE = 512


class User(object):
    def __init__(self, insurance_service, encrypter, decrypter):
        self.insurance_service = insurance_service
        self.encrypter = encrypter
        self.decrypter = decrypter
        self.secret_keys = {}
        self.owner_key_pairs = []
        self._global_parameters = None

    def issue_secret_keys(self, secret_keys):
        """
        Issue new secret keys to this user.
        :param secret_keys:
        :type secret_keys: dict

        >>> user = User()
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

    def create_owner_key_pair(self):
        key_pair = create_key_pair(RSA_KEY_SIZE)
        self.owner_key_pairs.append(key_pair)
        return key_pair

    def create_record(self, read_policy, write_policy, message):
        key = self.global_parameters.group.random(GT)
        symmetric_key = extract_key_from_group_element(self.global_parameters.group, key, 32)
        encryptor = AES.new(symmetric_key, AES.MODE_CBC, 'This is an IV456')
        owner_key_pair = self.create_owner_key_pair()
        write_key_pair = create_key_pair(RSA_KEY_SIZE)

        return CreateRecord(
            read_policy=read_policy,
            write_policy=write_policy,
            owner_public_key=owner_key_pair.publickey(),
            write_public_key=write_key_pair.publickey(),
            # encryption_key_read=
            # encryption_key_owner=
            # write_private_key=
            data=encryptor.encrypt(message)
        )
