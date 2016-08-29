import os

from os import path

from shared.implementations.serializer.base_serializer import BaseSerializer
from shared.model.records.data_record import DataRecord

STORAGE_DATA_DIRECTORY = 'data/storage'


class Storage(object):
    def __init__(self, serializer: BaseSerializer, storage_path: str = None) -> None:
        self.storage_path = STORAGE_DATA_DIRECTORY if storage_path is None else storage_path
        self.serializer = serializer
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)

    def store(self, name: str, record: DataRecord) -> None:
        """
        Store the data record.
        :param name: The location of the data record
        :param record: The record to store
        """
        f = open(path.join(self.storage_path, '%s.meta' % name), 'wb')
        f.write(self.serializer.serialize_data_record_meta(record))
        f.close()

        f = open(path.join(self.storage_path, '%s.dat' % name), 'wb')
        f.write(record.data)
        f.close()

    def load(self, name: str) -> DataRecord:
        """
        Load a data record from storage.
        :param name: The location of the data record
        :return: The loaded data record
        """
        f = open(path.join(self.storage_path, '%s.meta' % name), 'rb')
        result = self.serializer.deserialize_data_record_meta(f.read())
        f.close()

        f = open(path.join(self.storage_path, '%s.dat' % name), 'rb')
        result.data = f.read()
        f.close()
        return result
