import pickle
from typing import Dict

from Crypto.Hash import SHA

from authority.attribute_authority import AttributeAuthority
from service.storage import Storage
from shared.implementations.public_key.base_public_key import BasePublicKey
from shared.model.global_parameters import GlobalParameters
from shared.model.records.create_record import CreateRecord
from shared.model.records.data_record import DataRecord
from shared.model.records.policy_update_record import PolicyUpdateRecord
from shared.model.records.update_record import UpdateRecord
from shared.serializer.pickle_serializer import PickleSerializer


class InsuranceService(object):
    """
    The insurance service is the main portal for the clients and is responsible for validating
    signatures and storing the data records.
    """

    def __init__(self, serializer: PickleSerializer, global_parameters: GlobalParameters,
                 public_key_scheme: BasePublicKey, storage_path: str = None) -> None:
        self.global_parameters = global_parameters
        self.storage = Storage(serializer, storage_path)
        self.public_key_scheme = public_key_scheme
        self.authorities = dict()  # type: Dict[str, AttributeAuthority]

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
        self.storage.store(location, create_record)
        return location

    def update(self, location: str, update_record: UpdateRecord):
        """
        Update the data on the given location
        :param location: The location of the record to update the data of
        :param update_record: The UpdateRecord containing the updated data
        """
        current_record = self.load(location)
        assert current_record is not None, 'Only existing records can be updated'
        assert self.public_key_scheme.verify(current_record.write_public_key, update_record.signature,
                                             update_record.data), 'Signature should be valid'
        current_record.update(update_record)
        self.storage.store(location, current_record)

    def policy_update(self, location: str, policy_update_record: PolicyUpdateRecord):
        """
        Update the data on the given location
        :param location: The location of the record to update the policies of
        :param policy_update_record: The PolicyUpdateRecord containing the updated policies
        """
        current_record = self.load(location)
        assert current_record is not None, 'Only existing records can be updated'
        assert self.public_key_scheme.verify(current_record.owner_public_key, policy_update_record.signature,
                                             pickle.dumps((policy_update_record.read_policy,
                                                           policy_update_record.write_policy,
                                                           policy_update_record.time_period))), 'Signature should be valid'
        current_record.update_policy(policy_update_record)
        self.storage.store(location, current_record)

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
        return self.storage.load(location)
