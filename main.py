from implementations.rw15 import RW15
from scheme.user import User


class ABEHealthCare(object):
    def rw15(self):
        implementation = RW15()

        central_authority = implementation.create_central_authority()
        central_authority.setup()

        insurance_company = implementation.create_attribute_authority()
        national_database = implementation.create_attribute_authority()
        insurance_company.setup(central_authority, ['reviewer', 'administration'])
        national_database.setup(central_authority, ['doctor', 'radiologist'])

        doctor = User()
        doctor.issue_secret_keys(national_database.keygen(doctor, ['doctor']))

if __name__ == '__main__':
    abe = ABEHealthCare()
    abe.rw15()
