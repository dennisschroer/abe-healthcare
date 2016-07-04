from implementations.rw15 import RW15
from scheme.user import User
from scheme.insurance_service import InsuranceService


class ABEHealthCare(object):
    def rw15(self):
        implementation = RW15()

        central_authority = implementation.create_central_authority()
        central_authority.setup()

        insurance_company = implementation.create_attribute_authority('INSURANCE')
        national_database = implementation.create_attribute_authority('NDB')
        insurance_company.setup(central_authority, ['reviewer', 'administration'])
        national_database.setup(central_authority, ['doctor', 'radiologist'])

        insurance_service = InsuranceService(central_authority.global_parameters)
        insurance_service.add_authority(insurance_company)
        insurance_service.add_authority(national_database)

        abe_encryption = implementation.create_abe_encryption()
        abe_decryption = implementation.create_abe_decryption()

        doctor = User('doctor', insurance_service, abe_encryption, abe_decryption)
        doctor.issue_secret_keys(national_database.keygen(doctor, ['doctor@NDB']))
        doctor.issue_secret_keys(insurance_company.keygen(doctor, ['reviewer@INSURANCE']))

        bob = User('bob', insurance_service, abe_encryption, abe_decryption)
        create_record = bob.create_record('doctor@NDB and reviewer@INSURANCE', 'administration@INSURANCE', 'Hello World     ')

        print(create_record)

if __name__ == '__main__':
    abe = ABEHealthCare()
    abe.rw15()
