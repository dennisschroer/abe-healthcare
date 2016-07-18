from implementations.rw15 import RW15
from scheme.user import User
from scheme.insurance_service import InsuranceService
from os import listdir, path, makedirs
from os.path import isfile, join


class ABEHealthCare(object):
    def __init__(self):
        self.implementation = None
        self.central_authority = None
        self.insurance_company = None
        self.national_database = None
        self.insurance_service = None
        if not path.exists('data/input'):
            makedirs('data/input')
        if not path.exists('data/output'):
            makedirs('data/output')

    def rw15(self):
        self.implementation = RW15()
        self.run()

    def setup_central_authority(self):
        """
        Setup central authority
        :return:
        """
        self.central_authority = self.implementation.create_central_authority()
        self.central_authority.setup()

    def setup_attribute_authorities(self, insurance_attributes, national_attributes):
        """
        Setup attribute authorities
        """
        self.insurance_company = self.implementation.create_attribute_authority('INSURANCE')
        self.national_database = self.implementation.create_attribute_authority('NDB')
        self.insurance_company.setup(self.central_authority, insurance_attributes)
        self.national_database.setup(self.central_authority, national_attributes)

    def setup_service(self):
        """
        Setup service
        """
        self.insurance_service = InsuranceService(self.central_authority.global_parameters, self.implementation)
        self.insurance_service.add_authority(self.insurance_company)
        self.insurance_service.add_authority(self.national_database)

    def run(self):
        assert self.implementation is not None

        insurance_attributes = ['REVIEWER', 'ADMINISTRATION']
        national_attributes = ['DOCTOR', 'RADIOLOGIST']

        self.setup_central_authority()
        self.setup_attribute_authorities(insurance_attributes, national_attributes)
        self.setup_service()

        # Create doctor
        doctor = User('doctor', self.insurance_service, self.implementation)
        doctor.issue_secret_keys(self.national_database.keygen(doctor, ['DOCTOR@NDB']))
        doctor.issue_secret_keys(self.insurance_company.keygen(doctor, ['REVIEWER@INSURANCE']))

        # Create user
        bob = User('bob', self.insurance_service, self.implementation)

        for filename in [f for f in listdir('data/input') if isfile(join('data/input', f))]:
            print('Reading %s' % join('data/input', filename))
            # Encrypt a message
            file = open(join('data/input', filename), 'rb')
            create_record = bob.create_record('DOCTOR@NDB and REVIEWER@INSURANCE', 'ADMINISTRATION@INSURANCE', file.read())
            file.close()

            # create_record = bob.create_record('DOCTOR@NDB and REVIEWER@INSURANCE', 'ADMINISTRATION@INSURANCE', b'Hello world')

            # print('CreateRecord:')
            # print(create_record.encryption_key_read)

            # Send to insurance
            location = bob.send_create_record(create_record)

            # print('Location:')
            # print(location)

            # Give it to the doctor
            record = doctor.request_record(location)

            # print('Received record')
            # print(record.encryption_key_read)

            data = doctor.decrypt_record(record)

            print('Writing %s' % join('data/output', filename))
            file = open(join('data/output', filename), 'wb')
            file.write(data)
            file.close()

            # print('Decrypted data')
            # print(data)

            # https://pypi.python.org/pypi/psutil

if __name__ == '__main__':
    abe = ABEHealthCare()
    abe.rw15()
