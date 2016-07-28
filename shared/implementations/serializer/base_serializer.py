import pickle
from typing import Any

from charm.toolbox.pairinggroup import PairingGroup
from shared.implementations.public_key.base_public_key import BasePublicKey
from shared.model.types import AbeEncryption
from shared.model.records.data_record import DataRecord

DATA_RECORD_READ_POLICY = 'rp'
DATA_RECORD_WRITE_POLICY = 'wp'
DATA_RECORD_OWNER_PUBLIC_KEY = 'opk'
DATA_RECORD_WRITE_PUBLIC_KEY = 'wpk'
DATA_RECORD_ENCRYPTION_KEY_READ = 'ekr'
DATA_RECORD_ENCRYPTION_KEY_OWNER = 'eko'
DATA_RECORD_WRITE_SECRET_KEY = 'wsk'
DATA_RECORD_INFO = 'i'
DATA_RECORD_TIME_PERIOD = 't'


class BaseSerializer(object):
    def __init__(self, group: PairingGroup) -> None:
        self.group = group

    def serialize_abe_ciphertext(self, ciphertext: AbeEncryption) -> Any:
        """
        Serialize the ciphertext resulting form an attribute based encryption to an object which can be pickled.

        This is required because by default, instances of pairing.Element can not be pickled but have to be serialized.
        :return: An object, probably a dict, which can be pickled
        """
        raise NotImplementedError()

    def deserialize_abe_ciphertext(self, dictionary: Any) -> AbeEncryption:
        """
        Deserialize a (pickleable) dictionary back to a (non-pickleable) ciphertext.

        :return: The deserialized ciphertext.
        """
        raise NotImplementedError()

    def serialize_data_record_meta(self, data_record: DataRecord, public_key_scheme: BasePublicKey) -> bytes:
        """
        Serialize a data record
        :param data_record:
        :param public_key_scheme:
        :return: A generator which yields the serialized fields
        """

        return pickle.dumps({
            DATA_RECORD_READ_POLICY: data_record.read_policy,
            DATA_RECORD_WRITE_POLICY: data_record.write_policy,
            DATA_RECORD_OWNER_PUBLIC_KEY: public_key_scheme.export_key(data_record.owner_public_key),
            DATA_RECORD_WRITE_PUBLIC_KEY: public_key_scheme.export_key(data_record.write_public_key),
            DATA_RECORD_ENCRYPTION_KEY_READ: self.serialize_abe_ciphertext(data_record.encryption_key_read),
            DATA_RECORD_ENCRYPTION_KEY_OWNER: data_record.encryption_key_owner,
            DATA_RECORD_TIME_PERIOD: data_record.time_period,
            DATA_RECORD_INFO: data_record.info,
            DATA_RECORD_WRITE_SECRET_KEY: (
                self.serialize_abe_ciphertext(data_record.write_private_key[0]),
                data_record.write_private_key[1])
        })

    def deserialize_data_record_meta(self, byte_object: bytes, public_key_scheme: BasePublicKey) -> DataRecord:
        d = pickle.loads(byte_object)
        return DataRecord(
            read_policy=d[DATA_RECORD_READ_POLICY],
            write_policy=d[DATA_RECORD_WRITE_POLICY],
            owner_public_key=public_key_scheme.import_key(d[DATA_RECORD_OWNER_PUBLIC_KEY]),
            write_public_key=public_key_scheme.import_key(d[DATA_RECORD_WRITE_PUBLIC_KEY]),
            encryption_key_read=self.deserialize_abe_ciphertext(d[DATA_RECORD_ENCRYPTION_KEY_READ]),
            encryption_key_owner=d[DATA_RECORD_ENCRYPTION_KEY_OWNER],
            write_private_key=(self.deserialize_abe_ciphertext(d[DATA_RECORD_WRITE_SECRET_KEY][0]),
                               d[DATA_RECORD_WRITE_SECRET_KEY][1]),
            time_period=d[DATA_RECORD_TIME_PERIOD],
            info=d[DATA_RECORD_INFO],
            data=None
        )

    def attribute_replacement(self, dict: dict, keyword: str) -> int:
        """
        Determine a shorter identifier for the given keyword, and store it in the dict. If a keyword is already
        in the dictionary, the existing replacement identifier is used.
        :param dict: The dictionary with existing replacements.
        :param keyword: The keyword to replace.
        :return: int The replacement keyword. The dict is also updated.

        >>> i = BaseSerializer(None)
        >>> d = dict()
        >>> a = i.attribute_replacement(d, 'TEST123')
        >>> b = i.attribute_replacement(d, 'TEST123')
        >>> c = i.attribute_replacement(d, 'TEST')
        >>> a == b
        True
        >>> b == c
        False
        >>> d[a]
        'TEST123'
        >>> d[b]
        'TEST123'
        >>> d[c]
        'TEST'
        """
        for (key, value) in dict.items():
            if value == keyword:
                # Already in the dictionary
                return key
        # Not in dict
        key = len(dict)
        dict[key] = keyword
        return key

    def undo_attribute_replacement(self, dict: dict, replacement: int) -> str:
        """
        Undo the attribute replacement as result from the attribute replacement.
        :param dict: The dictionary with the replacements.
        :param replacement: The replacement to revert to the original keyword.
        :return: The original keyword.

        >>> i = BaseSerializer(None)
        >>> d = dict()
        >>> a = i.attribute_replacement(d, 'TEST123')
        >>> b = i.attribute_replacement(d, 'TEST')
        >>> i.undo_attribute_replacement(d, a) == 'TEST123'
        True
        >>> i.undo_attribute_replacement(d, b) == 'TEST'
        True
        >>> i.undo_attribute_replacement(d, 123)
        Traceback (most recent call last):
        ...
        KeyError: 123
        """
        return dict[replacement]
