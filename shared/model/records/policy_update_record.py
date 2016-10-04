from typing import Any, Tuple


class PolicyUpdateRecord(object):
    def __init__(self,
                 read_policy: str,
                 write_policy: str,
                 write_public_key: Any,
                 encryption_key_read: bytes,
                 encryption_key_owner: bytes,
                 write_private_key: Tuple[dict, bytes],
                 time_period: int,
                 info: bytes,
                 data: bytes,
                 signature: bytes
                 ) -> None:
        self.time_period = time_period
        self.info = info
        self.read_policy = read_policy
        self.write_policy = write_policy
        self.write_public_key = write_public_key
        self.encryption_key_read = encryption_key_read
        self.encryption_key_owner = encryption_key_owner
        self.write_private_key = write_private_key
        self.data = data
        self.signature = signature
