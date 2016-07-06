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
        :return: The central authority of this implementation.
        """
        raise NotImplementedError()

    def create_attribute_authority(self, name):
        """
        Create a new attribute authority.
        :param name: The name of the authority.
        :return: An attribute authority of this implementation
        """
        raise NotImplementedError()

    def setup_secret_keys(self, user):
        raise NotImplementedError()

    def update_secret_keys(self, base_keys, secret_keys):
        raise NotImplementedError()

    def abe_encrypt(self, global_parameters, public_keys, message, read_policy):
        raise NotImplementedError()

    def serialize_abe_ciphertext(self):
        raise NotImplementedError

    def abe_decrypt(self, global_parameters, secret_keys, message):
        raise NotImplementedError()

    def ske_encrypt(self, message, key):
        iv = Random.new().read(AES.block_size)
        encryption = AES.new(key, AES.MODE_CBC, iv)
        return iv + encryption.encrypt(pad_data_pksc5(message, AES.block_size))

    def ske_decrypt(self, ciphertext, key):
        iv = ciphertext[:AES.block_size]
        decryption = AES.new(key, AES.MODE_CBC, iv)
        return unpad_data_pksc5(decryption.decrypt(ciphertext[AES.block_size:]))

    def pke_generate_key_pair(self, size):
        """
        Create a new public and private key pair
        :param size: The size in bits
        :return: A new key pair

        >>> i = BaseImplementation()
        >>> i.pke_generate_key_pair(1024) is not None
        True
        """
        return RSA.generate(size)

    def pke_encrypt(self, message, key):
        encryption = PKCS1_OAEP.new(key)
        return encryption.encrypt(message)
