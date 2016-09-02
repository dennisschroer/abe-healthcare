from typing import Dict

from authority.attribute_authority import AttributeAuthority
from service.insurance_service import InsuranceService
from shared.connection.base_connection import BaseConnection
from shared.implementations.serializer.base_serializer import BaseSerializer
from shared.model.global_parameters import GlobalParameters
from shared.model.records.create_record import CreateRecord
from shared.model.records.data_record import DataRecord
from shared.model.records.policy_update_record import PolicyUpdateRecord
from shared.model.records.update_record import UpdateRecord


class UserInsuranceConnection(BaseConnection):
    def __init__(self, insurance_service: InsuranceService, serializer: BaseSerializer = None,
                 benchmark: bool = False) -> None:
        super().__init__(benchmark)
        self.insurance_service = insurance_service
        self.serializer = serializer

    def request_global_parameters(self) -> GlobalParameters:
        response = self.insurance_service.global_parameters
        if self.benchmark:
            self.add_benchmark('in request_global_parameters',
                               len(self.serializer.serialize_global_parameters(response)))
        return response

    def request_authorities(self) -> Dict[str, AttributeAuthority]:
        response = self.insurance_service.authorities
        if self.benchmark:
            self.add_benchmark('in request_authorities', len(self.serializer.serialize_authorities(response)))
        return response

    def request_record(self, location: str) -> DataRecord:
        response = self.insurance_service.load(location)
        if self.benchmark:
            self.add_benchmark('out request_record', len(location))
            self.add_benchmark('in request_record', len(self.serializer.serialize_data_record(response)))
        return response

    def send_create_record(self, create_record: CreateRecord) -> str:
        location = self.insurance_service.create(create_record)
        if self.benchmark:
            self.add_benchmark('out create_record', len(self.serializer.serialize_create_record(create_record)))
            self.add_benchmark('in create_record', len(location))
        return location

    def send_update_record(self, location: str, update_record: UpdateRecord) -> None:
        self.insurance_service.update(location, update_record)
        if self.benchmark:
            self.add_benchmark('out update_record', len(self.serializer.serialize_update_record(update_record)))

    def send_policy_update_record(self, location: str, policy_update_record: PolicyUpdateRecord) -> None:
        self.insurance_service.policy_update(location, policy_update_record)
        if self.benchmark:
            self.add_benchmark('out policy_update_record',
                               len(location) + len(
                                   self.serializer.serialize_policy_update_record(policy_update_record)))
