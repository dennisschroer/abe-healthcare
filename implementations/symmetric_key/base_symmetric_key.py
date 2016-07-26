class BaseSymmetricKey(object):
    def ske_key_size(self):
        """
        Get the size of the key to use in the symmetric key encryption scheme of this implementation.
        :return:
        """
        raise NotImplementedError()

    def ske_encrypt(self, message: bytes, key: bytes) -> bytes:
        """
        Encrypt the message using symmetric key encryption.
        :param message: The message to encrypt.
        :param key: The key to use in the encryption.
        :return: The encrypted message
        """
        raise NotImplementedError()

    def ske_decrypt(self, ciphertext: bytes, key: bytes) -> bytes:
        """
        Decrypt a ciphertext encrypted using symmetric key encryption of this implementation.
        :param ciphertext: The ciphertext to decrypt.
        :param key: The key to use.
        :return: The plaintext, or some random bytes.
        """
        raise NotImplementedError()
