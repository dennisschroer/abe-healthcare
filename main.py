from implementations.rw15 import RW15
from scheme.user import User
from scheme.insurance_service import InsuranceService


class ABEHealthCare(object):
    def rw15(self):
        implementation = RW15()

        central_authority = implementation.create_central_authority()
        central_authority.setup()

        insurance_company = implementation.create_attribute_authority()
        national_database = implementation.create_attribute_authority()
        insurance_company.setup(central_authority, ['reviewer', 'administration'])
        national_database.setup(central_authority, ['doctor', 'radiologist'])

        insurance_service = InsuranceService()

        doctor = User(insurance_service)
        doctor.issue_secret_keys(national_database.keygen(doctor, ['doctor']))
        doctor.issue_secret_keys(insurance_company.keygen(doctor, ['reviewer']))

        encrypter = implementation.create_encrypter()
        decrypter = implementation.create_decrypter()

        bob = User(insurance_service, encrypter, decrypter)
        create_record = bob.create_record('doctor and reviewer', None, 'Hello World')

if __name__ == '__main__':
    abe = ABEHealthCare()
    abe.rw15()
