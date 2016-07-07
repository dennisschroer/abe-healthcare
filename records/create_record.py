from collections import namedtuple

CreateRecord = namedtuple('CreateRecord', [
    'read_policy',
    'write_policy',
    'owner_public_key',
    'write_public_key',
    'encryption_key_read',
    'encryption_key_owner',
    'write_private_key',
    'data'
])