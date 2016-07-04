import base64
from Crypto.PublicKey import RSA


def extract_key_from_group_element(group, group_element, length):
    return base64.b64decode(group.serialize(group_element))[:length]


def create_key_pair(size):
    """
    Create a new public and private key pair
    :param size: The size in bits
    :return: A new key pair

    >>> create_key_pair(512) is not None
    True
    """
    return RSA.generate(size)
