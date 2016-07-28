from Crypto import Random
from Crypto.Cipher import AES

from shared.implementations.symmetric_key.base_symmetric_key import BaseSymmetricKey
from shared.utils.data_util import pad_data_pksc5, unpad_data_pksc5


class AESSymmetricKey(BaseSymmetricKey):
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

        >>> i = AESSymmetricKey()
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

        >>> i = AESSymmetricKey()
        >>> m = b'Hello world'
        >>> c = i.ske_encrypt(m, b'a'*i.ske_key_size())
        >>> d = i.ske_decrypt(c, b'a'*i.ske_key_size())
        >>> d == m
        True
        """
        iv = ciphertext[:AES.block_size]
        decryption = AES.new(key, AES.MODE_CBC, iv)
        return unpad_data_pksc5(decryption.decrypt(ciphertext[AES.block_size:]))