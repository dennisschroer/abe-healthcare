class DataRecord(object):
    def __init__(self, read_policy=None, write_policy=None, owner_public_key=None, write_public_key=None,
                 encryption_key_read=None, encryption_key_owner=None, write_private_key=None, data=None):
        self.read_policy = read_policy
        self.write_policy = write_policy
        self.owner_public_key = owner_public_key
        self.write_public_key = write_public_key
        self.encryption_key_read = encryption_key_read
        self.encryption_key_owner = encryption_key_owner
        self.write_private_key = write_private_key
        self.data = data
