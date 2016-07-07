from scheme.storage import Storage
import os


class InsuranceService(object):
    """
    The insurance service is the main portal for the clients and is responsible for validating
    signatures and storing the data records.
    """

    def __init__(self, global_parameters, implementation):
        self.global_parameters = global_parameters
        self.implementation = implementation
        self.storage = Storage()
        self.authorities = {}
        self.records = {}

    def add_authority(self, attribute_authority):
        """
        Add an attribute authority.
        :param attribute_authority: The attribute authority to add.
         :type attribute_authority: scheme.attribute_authority.AttributeAuthority
        """
        self.authorities[attribute_authority.name] = attribute_authority

    def merge_public_keys(self):
        result = {}
        for name in self.authorities:
            result[name] = self.authorities[name].public_keys
        return result

    def create(self, create_record):
        """
        Create a new data record
        :param create_record: The data record to create.
        :type create_record: records.data_record.DataRecord
        :return: The location of the record.
        """
        # In future possibly adapt and check the record
        name = self.add(create_record)
        self.store(name, create_record)
        return name

    def store(self, name, record):
        """
        Store the data record.
        :param name: The location of the data record
        :param record: The record to store
        :type record: records.data_record.DataRecord
        """
        if not os.path.exists('data/storage'):
            os.makedirs('data/storage')
        f = open('data/storage/%s.meta' % name, 'wb')
        f.write(self.storage.serialize_data_record_meta(record, self.implementation))
        f.close()

        f = open('data/storage/%s.dat' % name, 'wb')
        f.write(record.data)
        f.close()

    def add(self, record):
        """
        Add a data record.
        :param record: The data record to add
        :type record: records.data_record.DataRecord
        :return: The location of the record
        """
        name = 'test'
        self.records[name] = record
        return name

    def get(self, location):
        """
        Get a data record from the given location.
        :param location: The location of the record.
        :return: The record or None.

        >>> service = InsuranceService(None, None)
        >>> location = service.add({'data': 'TEST'})
        >>> service.get(location) is not None
        True
        >>> service.get(location) == {'data': 'TEST'}
        True
        """
        return self.records[location] if location in self.records else None
