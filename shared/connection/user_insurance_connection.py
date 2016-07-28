from service.insurance_service import InsuranceService


class UserInsuranceConnection(object):
    def __init__(self, insurance_service: InsuranceService):
        self.insurance_service = insurance_service

    def request_global_parameters(self):
        return self.insurance_service.global_parameters

    def request_authorities(self):
        return self.insurance_service.authorities

    def request_record(self, location):
        return self.insurance_service.load(location)

    def send_create_record(self, create_record):
        return self.insurance_service.create(create_record)

    def send_update_record(self, location, update_record):
        self.insurance_service.update(location, update_record)

    def send_policy_update_record(self, location, policy_update_record):
        self.insurance_service.policy_update(location, policy_update_record)
