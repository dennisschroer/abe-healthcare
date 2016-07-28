import os

from implementations.base_implementation import BaseImplementation
from model.records.data_record import DataRecord


class Storage(object):
    def __init__(self):
        if not os.path.exists('data/storage'):
            os.makedirs('data/storage')

    def store(self, name: str, record: DataRecord, implementation: BaseImplementation):
        """
        Store the data record.
        :param implementation: The implementation
        :param name: The location of the data record
        :param record: The record to store
        """
        serializer = implementation.create_serializer()
        pke = implementation.create_public_key_scheme()

        f = open('data/storage/%s.meta' % name, 'wb')
        f.write(serializer.serialize_data_record_meta(record, pke))
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
        serializer = implementation.create_serializer()
        pke = implementation.create_public_key_scheme()

        f = open('data/storage/%s.meta' % name, 'rb')
        result = serializer.deserialize_data_record_meta(f.read(), pke)
        f.close()

        f = open('data/storage/%s.dat' % name, 'rb')
        result.data = f.read()
        f.close()
        return result
