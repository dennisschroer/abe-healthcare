from implementations.base_implementation import BaseImplementation
from records.create_record import CreateRecord
from records.data_record import DataRecord
from records.global_parameters import GlobalParameters
from records.update_record import UpdateRecord
from scheme.attribute_authority import AttributeAuthority
from scheme.storage import Storage
from Crypto.Hash import SHA


class InsuranceService(object):
    """
    The insurance service is the main portal for the clients and is responsible for validating
    signatures and storing the data records.
    """

    def __init__(self, global_parameters: GlobalParameters, implementation: BaseImplementation):
        self.global_parameters = global_parameters
        self.implementation = implementation
        self.storage = Storage()
        self.authorities = {}

    def add_authority(self, attribute_authority: AttributeAuthority):
        """
        Add an attribute authority.
        :param attribute_authority: The attribute authority to add.
        """
        self.authorities[attribute_authority.name] = attribute_authority

    def create(self, create_record: CreateRecord) -> str:
        """
        Create a new data record
        :param create_record: The data record to create.
        :return: The location of the record.
        """
        # In future possibly adapt and check the record

        location = InsuranceService.determine_record_location(create_record)
        self.storage.store(location, create_record, self.implementation)
        return location

    def update(self, location: str, update_record: UpdateRecord):
        """
        Update the data on the given location
        :param location: The location to update the
        :param update_record: The UpdateRecord containing the updated data
        """
        current_record = self.load(location)
        assert current_record is not None, 'Only existing records can be updated'
        assert self.implementation.pke_verify(current_record.write_public_key, update_record.signature,
                                              update_record.data), 'Signature should be valid'
        current_record.update(update_record)
        self.storage.store(location, current_record, self.implementation)

    @staticmethod
    def determine_record_location(record: DataRecord) -> str:
        """
        Determine a unique location for a data record
        :param record: The data record
        :type record: records.data_record.DataRecord
        :return: A unique location
        """
        return SHA.new(record.info).hexdigest()

    def load(self, location: str) -> DataRecord:
        return self.storage.load(location, self.implementation)
