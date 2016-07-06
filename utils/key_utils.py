import base64
from Crypto.PublicKey import RSA


def extract_key_from_group_element(group, group_element, length):
    return base64.b64decode(group.serialize(group_element))[:length]
