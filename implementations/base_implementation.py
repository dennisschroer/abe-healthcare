from typing import Any, Dict, Tuple

from Crypto import Random
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

from charm.core.math.pairing import GT
from charm.toolbox.pairinggroup import PairingGroup
from records.global_parameters import GlobalParameters
from scheme.attribute_authority import AttributeAuthority
from scheme.central_authority import CentralAuthority
from scheme.user import User
from utils.data_util import pad_data_pksc5, unpad_data_pksc5
from utils.key_utils import extract_key_from_group_element

AbeEncryption = Any
SecretKeyStore = Any
SecretKeys = Any


class BaseImplementation(object):
    """
    The base implementation provider for different ABE implementations. Acts as an abstract factory for
    implementation specific subclasses of various scheme classes.
    """

    def __init__(self, group: PairingGroup = None) -> None:
        self.group = PairingGroup('SS512') if group is None else group

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

    def setup_secret_keys(self, username: str) -> SecretKeyStore:
        """
        Setup the secret key store for the given user.
        :param username: The name of the user
        :return: The key store for the given user.
        """
        raise NotImplementedError()

    def update_secret_keys(self, base_keys: SecretKeyStore, secret_keys: SecretKeys) -> None:
        """
        Add new keys to the secret keys of a user.
        :param base_keys:
        :param secret_keys:
        """
        raise NotImplementedError()

    def merge_public_keys(self, authorities: Dict[str, AttributeAuthority]) -> Dict[str, Any]:
        """
        Merge the public keys of the attribute authorities to a single entity containing all
        public keys.
        :param authorities: A dict from authority name to authority
        :return: A dict containing the public keys of the authorities.

        >>> from scheme.attribute_authority import AttributeAuthority
        >>> a1 = AttributeAuthority('A1')
        >>> a2 = AttributeAuthority('A2')
        >>> a1.public_keys = {'foo': 'bar'}
        >>> a2.public_keys = {'a': 'b'}
        >>> base_implementation = BaseImplementation()
        >>> public_keys = base_implementation.merge_public_keys({a1.name: a1, a2.name: a2})
        >>> public_keys == {'A1': {'foo': 'bar'}, 'A2': {'a': 'b'}}
        True
        """
        return {name: authority.public_keys for name, authority in authorities.items()}

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
                    policy: str) -> AbeEncryption:
        """
        Encrypt the message using attribute based encrpytion. This only works if message can be encrypted
        by the underlying implementation (in practice: element of a group).
        :param global_parameters: The global parameters.
        :param public_keys: The public keys of the authorities
        :param message: The message to encrypt.
        :param policy: The policy to encrypt under.
        :return: The encrypted message.
        """
        raise NotImplementedError()

    def abe_encrypt_wrapped(self, global_parameters: GlobalParameters, public_keys: Dict[str, Any], message: bytes,
                            policy: str) -> Tuple[AbeEncryption, bytes]:
        """
        Encrypt the message using attribute based encryption, by encrypting the message with symmetric encryption and
        the key with attribute based encryption.
        :param global_parameters: The global parameters.
        :param public_keys: The public keys of the authorities
        :param message: The message to encrypt.
        :param policy: The policy to encrypt under.
        :return: The encrypted key and the encrypted message.
        """
        key, symmetric_key = self.generate_abe_key(global_parameters)
        ciphertext = self.ske_encrypt(message, symmetric_key)
        encrypted_key = self.abe_encrypt(global_parameters, public_keys, key, policy)
        return encrypted_key, ciphertext

    def abe_decrypt(self, global_parameters: GlobalParameters, secret_keys: SecretKeyStore, ciphertext: AbeEncryption) -> bytes:
        """
        Decrypt some ciphertext resulting from an attribute based encryption to the plaintext.
        :param global_parameters: The global parameters.
        :param secret_keys: The secret keys of the user.
        :param ciphertext: The ciphertext to decrypt.
        :raise exception.policy_not_satisfied_exception.PolicyNotSatisfiedException: raised when the secret keys do not satisfy the access policy
        :return: The plaintext
        """
        raise NotImplementedError()

    def abe_decrypt_wrapped(self, global_parameters: GlobalParameters, secret_keys: SecretKeyStore, ciphertext_tuple: Tuple[AbeEncryption, bytes]):
        """
        Decrypt some ciphertext resulting from a wrapped attribute based encryption
        (encrypted with symmetric key encryption and attribute based encryption) to the plaintext.
        :param global_parameters: The global parameters.
        :type global_parameters: records.global_parameters.GlobalParameters
        :param secret_keys: The secret keys of the user.
        :param ciphertext_tuple: The ciphertext to decrypt. This is a tuple containing the encrypted key and the ciphertext
        encrypted using symmetric key encryption.
        :raise Exception: raised when the secret keys do not satisfy the access policy
        :return: The plaintext
        """
        encrypted_key, ciphertext = ciphertext_tuple
        key = self.abe_decrypt(global_parameters, secret_keys, encrypted_key)
        symmetric_key = extract_key_from_group_element(global_parameters.group, key,
                                                       self.ske_key_size())
        return self.ske_decrypt(ciphertext, symmetric_key)

    def serialize_abe_ciphertext(self, ciphertext: AbeEncryption) -> Any:
        """
        Serialize the ciphertext resulting form an attribute based encryption to an object which can be pickled.

        This is required because by default, instances of pairing.Element can not be pickled but have to be serialized.
        :return: An object, probably a dict, which can be pickled
        """
        raise NotImplementedError

    def deserialize_abe_ciphertext(self, dictionary: Any) -> AbeEncryption:
        """
        Deserialize a (pickleable) dictionary back to a (non-pickleable) ciphertext.

        :return: The deserialized ciphertext.
        """
        raise NotImplementedError

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

    def pke_generate_key_pair(self, size: int) -> Any:
        """
        Create a new public and private key pair
        :param size: The size in bits
        :return: A new key pair

        >>> i = BaseImplementation()
        >>> i.pke_generate_key_pair(1024) is not None
        True
        """
        return RSA.generate(size)

    def pke_import_key(self, data: bytes) -> Any:
        return RSA.importKey(data)

    def pke_encrypt(self, message: bytes, key: Any) -> bytes:
        """
        Encrypt a message using public key encryption.
        :param message: The message to encrypt
        :param key: The public key to encrypt with
        :return: The ciphertext
        """
        encryption = PKCS1_OAEP.new(key)
        return encryption.encrypt(message)

    def pke_sign(self, secret_key: Any, data: bytes) -> bytes:
        """
        Sign the data using the secret key
        :param secret_key:
        :param data:
        :return:

        >>> i = BaseImplementation()
        >>> m = b'Hello world'
        >>> key = i.pke_generate_key_pair(1024)
        >>> s = i.pke_sign(key, m)
        >>> s != m
        True
        """
        h = SHA.new(data)
        signer = PKCS1_v1_5.new(secret_key)
        return signer.sign(h)

    def pke_verify(self, public_key: Any, signature: bytes, data: bytes) -> bool:
        """
        Verify a signature over data with the given key.
        :param public_key:
        :param signature:
        :param data:
        :return:

        >>> i = BaseImplementation()
        >>> m = b'Hello world'
        >>> key = i.pke_generate_key_pair(1024)
        >>> s = i.pke_sign(key, m)
        >>> i.pke_verify(key.publickey(), s, m)
        True
        """
        h = SHA.new(data)
        signer = PKCS1_v1_5.new(public_key)
        return signer.verify(h, signature)

    def attribute_replacement(self, dict: dict, keyword: str) -> int:
        """
        Determine a shorter identifier for the given keyword, and store it in the dict. If a keyword is already
        in the dictionary, the existing replacement identifier is used.
        :param dict: The dictionary with existing replacements.
        :param keyword: The keyword to replace.
        :return: int The replacement keyword. The dict is also updated.

        >>> i = BaseImplementation()
        >>> d = dict()
        >>> a = i.attribute_replacement(d, 'TEST123')
        >>> b = i.attribute_replacement(d, 'TEST123')
        >>> c = i.attribute_replacement(d, 'TEST')
        >>> a == b
        True
        >>> b == c
        False
        >>> d[a]
        'TEST123'
        >>> d[b]
        'TEST123'
        >>> d[c]
        'TEST'
        """
        for (key, value) in dict.items():
            if value == keyword:
                # Already in the dictionary
                return key
        # Not in dict
        key = len(dict)
        dict[key] = keyword
        return key

    def undo_attribute_replacement(self, dict: dict, replacement: int) -> str:
        """
        Undo the attribute replacement as result from the attribute replacement.
        :param dict: The dictionary with the replacements.
        :param replacement: The replacement to revert to the original keyword.
        :return: The original keyword.

        >>> i = BaseImplementation()
        >>> d = dict()
        >>> a = i.attribute_replacement(d, 'TEST123')
        >>> b = i.attribute_replacement(d, 'TEST')
        >>> i.undo_attribute_replacement(d, a) == 'TEST123'
        True
        >>> i.undo_attribute_replacement(d, b) == 'TEST'
        True
        >>> i.undo_attribute_replacement(d, 123)
        Traceback (most recent call last):
        ...
        KeyError: 123
        """
        return dict[replacement]


class MockImplementation(BaseImplementation):
    """
    Mock implementation for testing purposes
    """

    def update_secret_keys(self, base: SecretKeyStore, secret_keys: SecretKeys) -> None:
        base.update(secret_keys)

    def setup_secret_keys(self, username: str) -> SecretKeyStore:
        return {}
