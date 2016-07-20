from typing import Any, Tuple

from records.update_record import UpdateRecord


class DataRecord(object):
    def __init__(self, read_policy: str = None,
                 write_policy: str = None,
                 owner_public_key: Any = None,
                 write_public_key: Any = None,
                 encryption_key_read: dict = None,
                 encryption_key_owner: bytes = None,
                 write_private_key: Tuple[dict, bytes] = None,
                 info: bytes = None, data: bytes = None) -> None:
        self.info = info
        self.read_policy = read_policy
        self.write_policy = write_policy
        self.owner_public_key = owner_public_key
        self.write_public_key = write_public_key
        self.encryption_key_read = encryption_key_read
        self.encryption_key_owner = encryption_key_owner
        self.write_private_key = write_private_key
        self.data = data

    def update(self, update_record: UpdateRecord):
        """
        Update this record with new data from an UpdateRecord

        :param update_record:
        :type update_record: records.update_record.UpdateRecord
        :return:
        """
        self.data = update_record.data
