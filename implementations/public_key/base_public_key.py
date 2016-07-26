from typing import Any


class BasePublicKey(object):
    def pke_generate_key_pair(self, size: int) -> Any:
        """
        Create a new public and private key pair
        :param size: The size in bits
        :return: A new key pair
        """
        raise NotImplementedError()

    def pke_import_key(self, data: bytes) -> Any:
        raise NotImplementedError()

    def pke_encrypt(self, message: bytes, key: Any) -> bytes:
        """
        Encrypt a message using public key encryption.
        :param message: The message to encrypt
        :param key: The public key to encrypt with
        :return: The ciphertext
        """
        raise NotImplementedError()

    def pke_sign(self, secret_key: Any, data: bytes) -> bytes:
        """
        Sign the data using the secret key
        :param secret_key:
        :param data:
        :return: The signature
        """
        raise NotImplementedError()

    def pke_verify(self, public_key: Any, signature: bytes, data: bytes) -> bool:
        """
        Verify a signature over data with the given key.
        :param public_key: The public key to use in the verification
        :param signature: The signature
        :param data: The data on which the signature is created
        :return: True if correct, False otherwise
        """
        raise NotImplementedError()

    def export(self, owner_public_key):
        raise NotImplementedError()
