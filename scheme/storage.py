import pickle
import os

from implementations.base_implementation import BaseImplementation
from records.data_record import DataRecord

DATA_RECORD_READ_POLICY = 'rp'
DATA_RECORD_WRITE_POLICY = 'wp'
DATA_RECORD_OWNER_PUBLIC_KEY = 'opk'
DATA_RECORD_WRITE_PUBLIC_KEY = 'wpk'
DATA_RECORD_ENCRYPTION_KEY_READ = 'ekr'
DATA_RECORD_ENCRYPTION_KEY_OWNER = 'eko'
DATA_RECORD_WRITE_SECRET_KEY = 'wsk'
DATA_RECORD_INFO = 'i'


class Storage(object):
    def __init__(self):
        if not os.path.exists('data/storage'):
            os.makedirs('data/storage')

    @staticmethod
    def serialize_data_record_meta(data_record: DataRecord, implementation: BaseImplementation) -> bytes:
        """
        Serialize a data record
        :param data_record:
        :type data_record: records.data_record.DataRecord
        :param implementation: The implementation of the scheme, used for serializing the ciphertext.
        :return: A generator which yields the serialized fields
        """
        return pickle.dumps({
            DATA_RECORD_READ_POLICY: data_record.read_policy,
            DATA_RECORD_WRITE_POLICY: data_record.write_policy,
            DATA_RECORD_OWNER_PUBLIC_KEY: data_record.owner_public_key.exportKey('DER'),
            DATA_RECORD_WRITE_PUBLIC_KEY: data_record.write_public_key.exportKey('DER'),
            DATA_RECORD_ENCRYPTION_KEY_READ: implementation.serialize_abe_ciphertext(data_record.encryption_key_read),
            DATA_RECORD_ENCRYPTION_KEY_OWNER: data_record.encryption_key_owner,
            DATA_RECORD_INFO: data_record.info,
            DATA_RECORD_WRITE_SECRET_KEY: (
                implementation.serialize_abe_ciphertext(data_record.write_private_key[0]),
                data_record.write_private_key[1])
        })

    @staticmethod
    def deserialize_data_record_meta(byte_object: bytes, implementation: BaseImplementation) -> DataRecord:
        d = pickle.loads(byte_object)
        return DataRecord(
            read_policy=d[DATA_RECORD_READ_POLICY],
            write_policy=d[DATA_RECORD_WRITE_POLICY],
            owner_public_key=implementation.pke_import_key(d[DATA_RECORD_OWNER_PUBLIC_KEY]),
            write_public_key=implementation.pke_import_key(d[DATA_RECORD_WRITE_PUBLIC_KEY]),
            encryption_key_read=implementation.deserialize_abe_ciphertext(d[DATA_RECORD_ENCRYPTION_KEY_READ]),
            encryption_key_owner=d[DATA_RECORD_ENCRYPTION_KEY_OWNER],
            write_private_key=(implementation.deserialize_abe_ciphertext(d[DATA_RECORD_WRITE_SECRET_KEY][0]),
                               d[DATA_RECORD_WRITE_SECRET_KEY][1]),
            info=d[DATA_RECORD_INFO],
            data=None
        )

    def store(self, name: str, record: DataRecord, implementation: BaseImplementation):
        """
        Store the data record.
        :param implementation: The implementation
        :param name: The location of the data record
        :param record: The record to store
        """
        f = open('data/storage/%s.meta' % name, 'wb')
        f.write(self.serialize_data_record_meta(record, implementation))
        f.close()

        f = open('data/storage/%s.dat' % name, 'wb')
        f.write(record.data)
        f.close()

    def load(self, name: str, implementation: BaseImplementation) -> DataRecord:
        """
        Load a data record from storage.
        :param name: The location of the data record
        :param implementation: The implementation
        :return: The loaded data record
        """
        f = open('data/storage/%s.meta' % name, 'rb')
        result = self.deserialize_data_record_meta(f.read(), implementation)
        f.close()

        f = open('data/storage/%s.dat' % name, 'rb')
        result.data = f.read()
        f.close()
        return result
