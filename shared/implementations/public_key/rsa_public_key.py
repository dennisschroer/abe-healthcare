from typing import Any

from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

from shared.implementations.public_key.base_public_key import BasePublicKey


class RSAPublicKey(BasePublicKey):
    def export_key(self, key):
        return key.exportKey('DER')

    def generate_key_pair(self, size: int) -> Any:
        """
        Create a new public and private key pair
        :param size: The size in bits
        :return: A new key pair

        >>> i = RSAPublicKey()
        >>> i.generate_key_pair(1024) is not None
        True
        """
        return RSA.generate(size)

    def import_key(self, data: bytes) -> Any:
        return RSA.importKey(data)

    def encrypt(self, message: bytes, key: Any) -> bytes:
        """
        Encrypt a message using public key encryption.
        :param message: The message to encrypt
        :param key: The public key to encrypt with
        :return: The ciphertext
        """
        encryption = PKCS1_OAEP.new(key)
        return encryption.encrypt(message)

    def sign(self, secret_key: Any, data: bytes) -> bytes:
        """
        Sign the data using the secret key
        :param secret_key:
        :param data:
        :return:

        >>> i = RSAPublicKey()
        >>> m = b'Hello world'
        >>> key = i.generate_key_pair(1024)
        >>> s = i.sign(key, m)
        >>> s != m
        True
        """
        h = SHA.new(data)
        signer = PKCS1_v1_5.new(secret_key)
        return signer.sign(h)

    def verify(self, public_key: Any, signature: bytes, data: bytes) -> bool:
        """
        Verify a signature over data with the given key.
        :param public_key:
        :param signature:
        :param data:
        :return:

        >>> i = RSAPublicKey()
        >>> m = b'Hello world'
        >>> key = i.generate_key_pair(1024)
        >>> s = i.sign(key, m)
        >>> i.verify(key.publickey(), s, m)
        True
        """
        h = SHA.new(data)
        signer = PKCS1_v1_5.new(public_key)
        return signer.verify(h, signature)
