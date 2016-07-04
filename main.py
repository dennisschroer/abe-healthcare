from implementations.rw15 import RW15
from scheme.user import User
from scheme.insurance_service import InsuranceService


class ABEHealthCare(object):
    def rw15(self):
        implementation = RW15()

        central_authority = implementation.create_central_authority()
        central_authority.setup()

        insurance_company = implementation.create_attribute_authority('Insurance')
        national_database = implementation.create_attribute_authority('NationalDB')
        insurance_company.setup(central_authority, ['reviewer', 'administration'])
        national_database.setup(central_authority, ['doctor', 'radiologist'])

        insurance_service = InsuranceService(central_authority.global_parameters)

        abe_encryption = implementation.create_abe_encryption()
        abe_decryption = implementation.create_abe_decryption()

        doctor = User(insurance_service, abe_encryption, abe_decryption)
        doctor.issue_secret_keys(national_database.keygen(doctor, ['doctor']))
        doctor.issue_secret_keys(insurance_company.keygen(doctor, ['reviewer']))



        bob = User(insurance_service, encrypter, decrypter)
        create_record = bob.create_record('doctor and reviewer', None, 'Hello World')

        print(create_record)

if __name__ == '__main__':
    abe = ABEHealthCare()
    abe.rw15()
