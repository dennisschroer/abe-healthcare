import sys
from typing import Dict

from authority.attribute_authority import AttributeAuthority
from service.insurance_service import InsuranceService
from shared.connection.base_connection import BaseConnection
from shared.model.global_parameters import GlobalParameters
from shared.model.records.create_record import CreateRecord
from shared.model.records.data_record import DataRecord
from shared.model.records.policy_update_record import PolicyUpdateRecord
from shared.model.records.update_record import UpdateRecord
from shared.serializer.pickle_serializer import PickleSerializer


class UserInsuranceConnection(BaseConnection):
    def __init__(self, insurance_service: InsuranceService, serializer: PickleSerializer, benchmark: bool = False) -> None:
        super().__init__(benchmark)
        self.insurance_service = insurance_service
        self.serializer = serializer

    def request_global_parameters(self) -> GlobalParameters:
        response = self.insurance_service.global_parameters
        if self.benchmark:
            print(self.serializer.global_parameters(response))
            self.add_benchmark('< request_global_parameters', len(self.serializer.global_parameters(response)))
        return response

    def request_authorities(self) -> Dict[str, AttributeAuthority]:
        response = self.insurance_service.authorities
        if self.benchmark:
            self.add_benchmark('< request_authorities', len(self.serializer.authorities(response)))
        return response

    def request_record(self, location: str) -> DataRecord:
        response = self.insurance_service.load(location)
        if self.benchmark:
            self.add_benchmark('> request_record', len(location))
            self.add_benchmark('< request_record', len(self.serializer.data_record(response)))
        return response

    def send_create_record(self, create_record: CreateRecord) -> str:
        location = self.insurance_service.create(create_record)
        if self.benchmark:
            self.add_benchmark('> send_create_record', len(self.serializer.create_record(create_record)))
            self.add_benchmark('< send_create_record', len(location))
        return location

    def send_update_record(self, location: str, update_record: UpdateRecord) -> None:
        self.insurance_service.update(location, update_record)
        if self.benchmark:
            self.add_benchmark('> send_update_record', len(self.serializer.update_record(update_record)))

    def send_policy_update_record(self, location: str, policy_update_record: PolicyUpdateRecord) -> None:
        self.insurance_service.policy_update(location, policy_update_record)
        if self.benchmark:
            self.add_benchmark('> send_policy_update_record.location', len(location))
            self.add_benchmark('> send_policy_update_record.record', len(self.serializer.policy_update_record(policy_update_record)))
