from typing import Any, Tuple

from model.records.update_record import UpdateRecord

from model.records.policy_update_record import PolicyUpdateRecord


class DataRecord(object):
    def __init__(self,
                 read_policy: str = None,
                 write_policy: str = None,
                 owner_public_key: Any = None,
                 write_public_key: Any = None,
                 encryption_key_read: dict = None,
                 encryption_key_owner: bytes = None,
                 write_private_key: Tuple[dict, bytes] = None,
                 time_period: int = None,
                 info: bytes = None,
                 data: bytes = None) -> None:
        self.time_period = time_period
        self.info = info
        self.read_policy = read_policy
        self.write_policy = write_policy
        self.owner_public_key = owner_public_key
        self.write_public_key = write_public_key
        self.encryption_key_read = encryption_key_read
        self.encryption_key_owner = encryption_key_owner
        self.write_private_key = write_private_key
        self.data = data

    def update(self, update_record: UpdateRecord) -> None:
        """
        Update this record with new data from an UpdateRecord

        :param update_record:
        :type update_record: records.update_record.UpdateRecord
        """
        self.data = update_record.data

    def update_policy(self, policy_update_record: PolicyUpdateRecord) -> None:
        """
        Update this record with new policies
        :param policy_update_record:
        """
        self.info = policy_update_record.info
        self.time_period = policy_update_record.time_period
        self.read_policy = policy_update_record.read_policy
        self.write_policy = policy_update_record.write_policy
        self.write_public_key = policy_update_record.write_public_key
        self.encryption_key_read = policy_update_record.encryption_key_read
        self.encryption_key_owner = policy_update_record.encryption_key_owner
        self.write_private_key = policy_update_record.write_private_key
        self.data = policy_update_record.data
