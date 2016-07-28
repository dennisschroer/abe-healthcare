import sys

from service.insurance_service import InsuranceService
from shared.connection.base_connection import BaseConnection


class UserInsuranceConnection(BaseConnection):
    def __init__(self, insurance_service: InsuranceService, benchmark=False):
        super().__init__(benchmark)
        self.insurance_service = insurance_service

    def request_global_parameters(self):
        response = self.insurance_service.global_parameters
        if self.benchmark:
            self.add_benchmark('< request_global_parameters', sys.getsizeof(response))
        return response

    def request_authorities(self):
        response = self.insurance_service.authorities
        if self.benchmark:
            self.add_benchmark('< request_authorities', sys.getsizeof(response))
        return response

    def request_record(self, location):
        response = self.insurance_service.load(location)
        if self.benchmark:
            self.add_benchmark('> request_record', sys.getsizeof(location))
            self.add_benchmark('< request_record', sys.getsizeof(response))
        return response

    def send_create_record(self, create_record):
        response = self.insurance_service.create(create_record)
        if self.benchmark:
            self.add_benchmark('> send_create_record', sys.getsizeof(create_record))
            self.add_benchmark('< send_create_record', sys.getsizeof(response))
        return response

    def send_update_record(self, location, update_record):
        self.insurance_service.update(location, update_record)
        if self.benchmark:
            self.add_benchmark('> send_update_record', sys.getsizeof(location))
            self.add_benchmark('> send_update_record', sys.getsizeof(update_record))

    def send_policy_update_record(self, location, policy_update_record):
        self.insurance_service.policy_update(location, policy_update_record)
        if self.benchmark:
            self.add_benchmark('> send_policy_update_record', sys.getsizeof(location))
            self.add_benchmark('> send_policy_update_record', sys.getsizeof(policy_update_record))

