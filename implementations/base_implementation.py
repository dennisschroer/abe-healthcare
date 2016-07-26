from typing import Any, Dict, Tuple

from Crypto import Random
from Crypto.Cipher import AES

from authority.attribute_authority import AttributeAuthority
from charm.core.math.pairing import GT
from charm.toolbox.pairinggroup import PairingGroup
from implementations.public_key.base_public_key import BasePublicKey
from implementations.public_key.rsa_pke import RSAPublicKey
from implementations.serializer.base_serializer import BaseSerializer
from model.records.global_parameters import GlobalParameters
from model.types import SecretKeyStore, SecretKeys, AbeEncryption
from service.central_authority import CentralAuthority
from utils.data_util import pad_data_pksc5, unpad_data_pksc5
from utils.key_utils import extract_key_from_group_element


class BaseImplementation(object):
    """
    The base implementation provider for different ABE implementations. Acts as an abstract factory for
    implementation specific subclasses of various scheme classes.
    """

    decryption_keys_required = False

    def __init__(self, group: PairingGroup = None) -> None:
        self.group = PairingGroup('SS512') if group is None else group
        self._public_key_scheme = None

    def create_central_authority(self) -> CentralAuthority:
        """
        Create a new central authority.
        :return: The central authority of this implementation.
        """
        raise NotImplementedError()

    def create_attribute_authority(self, name: str) -> AttributeAuthority:
        """
        Create a new attribute authority.
        :param name: The name of the authority.
        :return: An attribute authority of this implementation
        """
        raise NotImplementedError()

    def create_serializer(self) -> BaseSerializer:
        """
        Create a new serializer.
        :return:  A new BaseSerializer
        """
        raise NotImplementedError()

    def create_public_key_scheme(self) -> BasePublicKey:
        """
        Create a new public key scheme
        :return: A BasePublicKey
        """
        if self._public_key_scheme is None:
            self._public_key_scheme = RSAPublicKey()
        return self._public_key_scheme

    def setup_secret_keys(self, gid: str) -> SecretKeyStore:
        """
        Setup the secret key store for the given user.
        :param gid: The gid of the user
        :return: The key store for the given user.
        """
        return {}

    def update_secret_keys(self, base_keys: SecretKeyStore, secret_keys: SecretKeys) -> None:
        """
        Add new keys to the secret keys of a user.
        :param base_keys:
        :param secret_keys:
        """
        base_keys.update(secret_keys)

    def merge_public_keys(self, authorities: Dict[str, AttributeAuthority], time_period: int) -> Dict[str, Any]:
        """
        Merge the public keys of the attribute authorities to a single entity containing all
        public keys.
        :param time_period: The time period to get the public of.
        :param authorities: A dict from authority name to authority
        :return: A dict containing the public keys of the authorities.

        >>> from authority.attribute_authority import AttributeAuthority
        >>> a1 = AttributeAuthority('A1')
        >>> a2 = AttributeAuthority('A2')
        >>> a1._public_keys = {'foo': 'bar'}
        >>> a2._public_keys = {'a': 'b'}
        >>> base_implementation = BaseImplementation()
        >>> public_keys = base_implementation.merge_public_keys({a1.name: a1, a2.name: a2}, 1)
        >>> public_keys == {'A1': {'foo': 'bar'}, 'A2': {'a': 'b'}}
        True
        """
        return {name: authority.public_keys_for_time_period(time_period) for name, authority in authorities.items()}

    def generate_abe_key(self, global_parameters: GlobalParameters) -> Tuple[Any, bytes]:
        """
        Generate a random key and the extracted symmetric key to be used in attribute based encryption.
        The first key can be encrypted using attribute based encryption, while the second can be applied in symmetric encryption.
        :param global_parameters: The global parameters
        :return: The key (element of group) and the extracted symmetric key
        """
        key = global_parameters.group.random(GT)
        symmetric_key = extract_key_from_group_element(global_parameters.group, key,
                                                       self.ske_key_size())
        return key, symmetric_key

    def abe_encrypt(self, global_parameters: GlobalParameters, public_keys: Dict[str, Any], message: bytes,
                    policy: str, time_period: int) -> AbeEncryption:
        """
        Encrypt the message using attribute based encryption. This only works if message can be encrypted
        by the underlying implementation (in practice: element of a group).
        :param time_period: The time period for which to encrypt.
        :param global_parameters: The global parameters.
        :param public_keys: The public keys of the authorities
        :param message: The message to encrypt.
        :param policy: The policy to encrypt under.
        :return: The encrypted message.
        """
        raise NotImplementedError()

    def abe_encrypt_wrapped(self, global_parameters: GlobalParameters, public_keys: Dict[str, Any], message: bytes,
                            policy: str, time_period: int) -> Tuple[AbeEncryption, bytes]:
        """
        Encrypt the message using attribute based encryption, by encrypting the message with symmetric encryption and
        the key with attribute based encryption.
        :param time_period: The time period for which to encrypt.
        :param global_parameters: The global parameters.
        :param public_keys: The public keys of the authorities
        :param message: The message to encrypt.
        :param policy: The policy to encrypt under.
        :return: The encrypted key and the encrypted message.
        """
        key, symmetric_key = self.generate_abe_key(global_parameters)
        ciphertext = self.ske_encrypt(message, symmetric_key)
        encrypted_key = self.abe_encrypt(global_parameters, public_keys, key, policy, time_period)
        return encrypted_key, ciphertext

    def decryption_keys(self, authorities: Dict[str, AttributeAuthority], secret_keys: SecretKeyStore,
                        time_period: int):
        """
        Calculate decryption keys for a user for the given attribute authority.
        :param authorities: The attribute authorities to fetch update keys of.
        :param secret_keys: The secret keys of the user.
        :param time_period: The time period to calculate the decryption keys for.
        :return: The decryption keys for the attributes of the authority the user possesses at the given time period.
        """
        raise NotImplementedError()

    def abe_decrypt(self, global_parameters: GlobalParameters, secret_keys: SecretKeyStore, gid: str,
                    ciphertext: AbeEncryption) -> bytes:
        """
        Decrypt some ciphertext resulting from an attribute based encryption to the plaintext.
        :param global_parameters: The global parameters.
        :param secret_keys: The secret keys of the user.
        :param gid: The global identifier of the user
        :param ciphertext: The ciphertext to decrypt.
        :raise exception.policy_not_satisfied_exception.PolicyNotSatisfiedException: raised when the secret keys do not satisfy the access policy
        :return: The plaintext
        """
        raise NotImplementedError()

    def abe_decrypt_wrapped(self, global_parameters: GlobalParameters, secret_keys: SecretKeyStore,
                            gid: str,
                            ciphertext_tuple: Tuple[AbeEncryption, bytes]):
        """
        Decrypt some ciphertext resulting from a wrapped attribute based encryption
        (encrypted with symmetric key encryption and attribute based encryption) to the plaintext.
        :param global_parameters: The global parameters.
        :type global_parameters: records.global_parameters.GlobalParameters
        :param secret_keys: The secret keys of the user.
        :param gid: The global identifier of the user
        :param ciphertext_tuple: The ciphertext to decrypt. This is a tuple containing the encrypted key and the ciphertext
        encrypted using symmetric key encryption.
        :raise Exception: raised when the secret keys do not satisfy the access policy
        :return: The plaintext
        """
        encrypted_key, ciphertext = ciphertext_tuple
        key = self.abe_decrypt(global_parameters, secret_keys, gid, encrypted_key)
        symmetric_key = extract_key_from_group_element(global_parameters.group, key,
                                                       self.ske_key_size())
        return self.ske_decrypt(ciphertext, symmetric_key)

    def ske_key_size(self):
        """
        Get the size of the key to use in the symmetric key encryption scheme of this implementation.
        :return:
        """
        return 32

    def ske_encrypt(self, message: bytes, key: bytes) -> bytes:
        """
        Encrypt the message using symmetric key encryption.
        :param message: The message to encrypt.
        :param key: The key to use in the encryption.
        :return: The encrypted message

        >>> i = BaseImplementation()
        >>> i.ske_encrypt(b'Hello world', b'a'*i.ske_key_size()) != b'Hello world'
        True
        """
        iv = Random.new().read(AES.block_size)
        encryption = AES.new(key, AES.MODE_CBC, iv)
        return iv + encryption.encrypt(pad_data_pksc5(message, AES.block_size))

    def ske_decrypt(self, ciphertext: bytes, key: bytes) -> bytes:
        """
        Decrypt a ciphertext encrypted using symmetric key encryption of this implementation.
        :param ciphertext: The ciphertext to decrypt.
        :param key: The key to use.
        :return: The plaintext, or some random bytes.

        >>> i = BaseImplementation()
        >>> m = b'Hello world'
        >>> c = i.ske_encrypt(m, b'a'*i.ske_key_size())
        >>> d = i.ske_decrypt(c, b'a'*i.ske_key_size())
        >>> d == m
        True
        """
        iv = ciphertext[:AES.block_size]
        decryption = AES.new(key, AES.MODE_CBC, iv)
        return unpad_data_pksc5(decryption.decrypt(ciphertext[AES.block_size:]))


class MockImplementation(BaseImplementation):
    """
    Mock implementation for testing purposes
    """

    def update_secret_keys(self, base: SecretKeyStore, secret_keys: SecretKeys) -> None:
        base.update(secret_keys)

    def setup_secret_keys(self, gid: str) -> SecretKeyStore:
        return {}
