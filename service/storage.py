import os

from shared.model.records.data_record import DataRecord
from shared.serializer.pickle_serializer import PickleSerializer


class Storage(object):
    def __init__(self, serializer: PickleSerializer) -> None:
        self.serializer = serializer
        if not os.path.exists('data/storage'):
            os.makedirs('data/storage')

    def store(self, name: str, record: DataRecord) -> None:
        """
        Store the data record.
        :param name: The location of the data record
        :param record: The record to store
        """
        f = open('data/storage/%s.meta' % name, 'wb')
        f.write(self.serializer.serialize_data_record_meta(record))
        f.close()

        f = open('data/storage/%s.dat' % name, 'wb')
        f.write(record.data)
        f.close()

    def load(self, name: str) -> DataRecord:
        """
        Load a data record from storage.
        :param name: The location of the data record
        :param implementation: The implementation
        :return: The loaded data record
        """
        f = open('data/storage/%s.meta' % name, 'rb')
        result = self.serializer.deserialize_data_record_meta(f.read())
        f.close()

        f = open('data/storage/%s.dat' % name, 'rb')
        result.data = f.read()
        f.close()
        return result
