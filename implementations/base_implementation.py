from charm.toolbox.pairinggroup import PairingGroup
from utils.data_util import pad_data_pksc5, unpad_data_pksc5
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto import Random


class BaseImplementation(object):
    """
    The base implementation provider for different ABE implementations. Acts as an abstract factory for
    implementation specific subclasses of various scheme classes.
    """

    def __init__(self, group=None):
        self.group = PairingGroup('SS512') if group is None else group

    def create_central_authority(self):
        """
        Create a new central authority.
        :return: scheme.central_authority.CentralAuthority The central authority of this implementation.
        """
        raise NotImplementedError()

    def create_attribute_authority(self, name):
        """
        Create a new attribute authority.
        :param name: The name of the authority.
        :return: scheme.attribute_authority.AttributeAuthority An attribute authority of this implementation
        """
        raise NotImplementedError()

    def setup_secret_keys(self, user):
        """
        Setup the secret key store for the given user.
        :param user:
        :return: The key store for the given user.
        """
        raise NotImplementedError()

    def update_secret_keys(self, base_keys, secret_keys):
        """
        Add new keys to the secret keys of a user.
        :param secret_keys_base:
        :param secret_keys:
        """
        raise NotImplementedError()

    def abe_encrypt(self, global_parameters, public_keys, message, policy):
        """
        Encrypt the message using attribute based encrpytion.
        :param global_parameters: The global parameters of the scheme
        :param public_keys: The public keys of the authorities
        :param message: The message to encrypt.
        :param policy: The policy to encrypt under.
        :return: The encrypted message.
        """
        raise NotImplementedError()

    def serialize_abe_ciphertext(self):
        """
        Serialize the ciphertext resulting form an attribute based encryption to an object which can be pickled.

        This is required because by default, instances of pairing.Element can not be pickled but have to be serialized.
        :return: An object, probably a dict, which can be pickled
        """
        raise NotImplementedError

    def abe_decrypt(self, global_parameters, secret_keys, ciphertext):
        """
        Decrypt some ciphertext resulting from an attribute based encryption to the plaintext.
        :param global_parameters: The global parameters of the scheme.
        :param secret_keys: The secret keys of the user.
        :param ciphertext: The ciphertext to decrypt.
        :raise Exception: raised when the secret keys do not satisfy the access policy
        :return: The plaintext
        """
        raise NotImplementedError()

    def ske_key_size(self):
        """
        Get the size of the key to use in the symmetric key encryption scheme of this implementation.
        :return:
        """
        return 32

    def ske_encrypt(self, message, key):
        """
        Encrypt the message using symmetric key encryption.
        :param message: The message to encrypt.
        :param key: The key to use in the encryption.
        :return: The encrypted message

        >>> i = BaseImplementation(None, None)
        >>> i.ske_encrypt("Hello world", 'a'*i.ske_key_size()) != "Hello world"
        True
        """
        iv = Random.new().read(AES.block_size)
        encryption = AES.new(key, AES.MODE_CBC, iv)
        return iv + encryption.encrypt(pad_data_pksc5(message, AES.block_size))

    def ske_decrypt(self, ciphertext, key):
        """
        Decrypt a ciphertext encrypted using symmetric key encryption of this implementation.
        :param ciphertext: The ciphertext to decrypt.
        :param key: The key to use.
        :return: The plaintext, or some random bytes.

        >>> i = BaseImplementation(None, None)
        >>> m = "Hello world"
        >>> c = i.ske_encrypt(m, 'a'*i.ske_key_size())
        >>> d = i.ske_decrypt(c, 'a'*i.ske_key_size())
        >>> d == m
        True
        """
        iv = ciphertext[:AES.block_size]
        decryption = AES.new(key, AES.MODE_CBC, iv)
        return unpad_data_pksc5(decryption.decrypt(ciphertext[AES.block_size:]))

    def pke_generate_key_pair(self, size):
        """
        Create a new public and private key pair
        :param size: The size in bits
        :return: A new key pair

        >>> i = BaseImplementation(None, None)
        >>> i.pke_generate_key_pair(1024) is not None
        True
        """
        return RSA.generate(size)

    def pke_encrypt(self, message, key):
        """
        Encrypt a message using public key encryption.
        :param message: The message to encrypt
        :param key: The public key to encrypt with
        :return: The ciphertext
        """
        encryption = PKCS1_OAEP.new(key)
        return encryption.encrypt(message)

    def attribute_replacement(self, dict, keyword):
        """
        Determine a shorter identifier for the given keyword, and store it in the dict. If a keyword is already
        in the dictionary, the existing replacement identifier is used.
        :param dict: The dictionary with existing replacements.
        :param keyword: The keyword to replace.
        :return: int The replacement keyword. The dict is also updated.

        >>> i = BaseImplementation(None, None)
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
        for (key, value) in dict.iteritems():
            if value == keyword:
                # Already in the dictionary
                return key
        # Not in dict
        key = len(dict)
        dict[key] = value
        return key

