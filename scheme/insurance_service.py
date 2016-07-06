from scheme.storage import Storage
import os

class InsuranceService(object):
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
        # In future possibly adapt and check the record
        name = self.add(create_record)
        self.store(name, create_record)
        return name

    def store(self, name, record):
        if not os.path.exists('data/storage'):
            os.makedirs('data/storage')
        f = open('data/storage/%s.meta' % name, 'wb')
        f.write(self.storage.serialize_data_record_meta(record, self.implementation))
        f.close()

        f = open('data/storage/%s.dat' % name, 'wb')
        f.write(record.data)
        f.close()

    def add(self, record):
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
