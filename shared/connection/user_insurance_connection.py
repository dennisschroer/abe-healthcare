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


class UserInsuranceConnection(BaseConnection):
    def __init__(self, insurance_service: InsuranceService, benchmark: bool = False) -> None:
        super().__init__(benchmark)
        self.insurance_service = insurance_service

    def request_global_parameters(self) -> GlobalParameters:
        response = self.insurance_service.global_parameters
        if self.benchmark:
            self.add_benchmark('< request_global_parameters', sys.getsizeof(response.scheme_parameters))
        return response

    def request_authorities(self) -> Dict[str, AttributeAuthority]:
        response = self.insurance_service.authorities
        if self.benchmark:
            self.add_benchmark('< request_authorities', sys.getsizeof(response))
        return response

    def request_record(self, location: str) -> DataRecord:
        response = self.insurance_service.load(location)
        if self.benchmark:
            self.add_benchmark('> request_record', sys.getsizeof(location))
            self.add_benchmark('< request_record', sys.getsizeof(response))
        return response

    def send_create_record(self, create_record: CreateRecord) -> str:
        response = self.insurance_service.create(create_record)
        if self.benchmark:
            self.add_benchmark('> send_create_record', sys.getsizeof(create_record))
            self.add_benchmark('> send_create_record.data', sys.getsizeof(create_record.data))
            self.add_benchmark('< send_create_record', sys.getsizeof(response))
        return response

    def send_update_record(self, location: str, update_record: UpdateRecord) -> None:
        self.insurance_service.update(location, update_record)
        if self.benchmark:
            self.add_benchmark('> send_update_record', sys.getsizeof(location))
            self.add_benchmark('> send_update_record', sys.getsizeof(update_record))

    def send_policy_update_record(self, location: str, policy_update_record: PolicyUpdateRecord) -> None:
        self.insurance_service.policy_update(location, policy_update_record)
        if self.benchmark:
            self.add_benchmark('> send_policy_update_record', sys.getsizeof(location))
            self.add_benchmark('> send_policy_update_record', sys.getsizeof(policy_update_record))
