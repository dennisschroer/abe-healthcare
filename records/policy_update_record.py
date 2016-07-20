from typing import Any, Tuple


class PolicyUpdateRecord(object):
    def __init__(self,
                 read_policy: str = None,
                 write_policy: str = None,
                 write_public_key: Any = None,
                 encryption_key_read: dict = None,
                 encryption_key_owner: bytes = None,
                 write_private_key: Tuple[dict, bytes] = None,
                 info: bytes = None,
                 data: bytes = None,
                 signature: bytes = None
                 ) -> None:
        self.info = info
        self.read_policy = read_policy
        self.write_policy = write_policy
        self.write_public_key = write_public_key
        self.encryption_key_read = encryption_key_read
        self.encryption_key_owner = encryption_key_owner
        self.write_private_key = write_private_key
        self.data = data
        self.signature = signature
