from collections import namedtuple

DataRecord = namedtuple('DataRecord', [
    'read_policy',
    'write_policy',
    'owner_public_key',
    'write_public_key',
    'encryption_key_read',
    'encryption_key_owner',
    'write_private_key',
    'data'
])
