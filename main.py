from implementations.rw15 import RW15
from scheme.user import User
from scheme.insurance_service import InsuranceService


class ABEHealthCare(object):
    def __init__(self):
        self.implementation = None

    def rw15(self):
        self.implementation = RW15()
        self.run()

    def run(self):
        assert self.implementation is not None

        # Setup central authority
        central_authority = self.implementation.create_central_authority()
        central_authority.setup()

        # Setup attribute authorities
        insurance_company = self.implementation.create_attribute_authority('INSURANCE')
        national_database = self.implementation.create_attribute_authority('NDB')
        insurance_company.setup(central_authority, ['REVIEWER', 'ADMINISTRATION'])
        national_database.setup(central_authority, ['DOCTOR', 'RADIOLOGIST'])

        # Setup service
        insurance_service = InsuranceService(central_authority.global_parameters)
        insurance_service.add_authority(insurance_company)
        insurance_service.add_authority(national_database)

        # Create doctor
        doctor = User('doctor', insurance_service, self.implementation)
        doctor.issue_secret_keys(national_database.keygen(doctor, ['DOCTOR@NDB']))
        doctor.issue_secret_keys(insurance_company.keygen(doctor, ['REVIEWER@INSURANCE']))

        # Create user
        bob = User('bob', insurance_service, self.implementation)

        # Encrypt a message
        create_record = bob.create_record('DOCTOR@NDB and REVIEWER@INSURANCE', 'ADMINISTRATION@INSURANCE', b'Hello World')

        print('CreateRecord:')
        print(create_record)

        # Send to insurance
        location = bob.send_create_record(create_record)

        print('Location:')
        print(location)

        # Give it to the doctor
        record = doctor.request_record(location)

        print('Received record')
        print(record)

        data = doctor.decrypt_record(record)

        print('Decrypted data')
        print(data)

if __name__ == '__main__':
    abe = ABEHealthCare()
    abe.rw15()
