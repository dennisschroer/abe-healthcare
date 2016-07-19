from scheme.storage import Storage
from Crypto.Hash import SHA


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

    def add_authority(self, attribute_authority):
        """
        Add an attribute authority.
        :param attribute_authority: The attribute authority to add.
         :type attribute_authority: scheme.attribute_authority.AttributeAuthority
        """
        self.authorities[attribute_authority.name] = attribute_authority

    def create(self, create_record):
        """
        Create a new data record
        :param create_record: The data record to create.
        :type create_record: records.data_record.DataRecord
        :return: The location of the record.
        """
        # In future possibly adapt and check the record

        location = self.determine_record_location(create_record)
        self.storage.store(location, create_record, self.implementation)
        return location

    def update(self, location, update_record):
        """
        Update the data on the given location
        :param location: The location to update the
        :param update_record: The UpdateRecord containing the updated data
        :type update_record: records.update_record.UpdateRecord
        """
        current_record = self.load(location)
        assert current_record is not None, 'Only existing records can be updated'
        assert self.implementation.pke_verify(current_record.write_public_key, update_record.signature,
                                              update_record.data), 'Signature should be valid'
        current_record.update(update_record)
        self.storage.store(location, current_record, self.implementation)

    def determine_record_location(self, record):
        """
        Determine a unique location for a data record
        :param record: The data record
        :type record: records.data_record.DataRecord
        :return: A unique location
        """
        return SHA.new(record.info).hexdigest()

    def load(self, location):
        return self.storage.load(location, self.implementation)
