from implementations.rw15 import RW15
from scheme.user import User
from scheme.insurance_service import InsuranceService
from os import listdir, path, makedirs
from os.path import isfile, join
# import psutil
import cProfile

from utils.random_file_generator import RandomFileGenerator


class ABEHealthCare(object):
    def __init__(self):
        self.implementation = None
        self.central_authority = None
        self.insurance_company = None
        self.national_database = None
        self.insurance_service = None
        self.doctor = None
        self.bob = None
        self.check_paths()

    def check_paths(self):
        if not path.exists('data/input'):
            makedirs('data/input')
        if not path.exists('data/storage'):
            makedirs('data/storage')
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

    def create_user(self, name, insurance_attributes=None, national_attributes=None):
        user = User(name, self.insurance_service, self.implementation)
        if insurance_attributes is not None:
            user.issue_secret_keys(self.insurance_company.keygen(user.gid, insurance_attributes))
        if national_attributes is not None:
            user.issue_secret_keys(self.national_database.keygen(user.gid, national_attributes))
        return user

    def run(self):
        self.setup()
        locations = self.run_encryptions()
        self.run_updates(locations)
        self.run_decryptions(locations)

    def setup(self):
        assert self.implementation is not None

        insurance_attributes = ['REVIEWER@INSURANCE', 'ADMINISTRATION@INSURANCE']
        national_attributes = ['DOCTOR@NDB', 'RADIOLOGIST@NDB']

        self.setup_central_authority()
        self.setup_attribute_authorities(insurance_attributes, national_attributes)
        self.setup_service()

        self.doctor = self.create_user('doctor', ['REVIEWER@INSURANCE', 'ADMINISTRATION@INSURANCE'], ['DOCTOR@NDB'])
        self.bob = self.create_user('bob')

    def encrypt_file(self, user, filename):
        """
        Encrypt a file with the policies in the file with '.policy' appended. The policy file contains two lines.
        The first line is the read policy, the second line the write policy.
        :param user: The user to encrypt with
        :type user: scheme.user.User
        :param filename: The filename (relative to /data/input) to encrypt
        :return: The name of the encrypted data (in /data/storage/)
        """
        # if filename.endswith(".policy"):
        #     continue
        policy_filename = '%s.policy' % filename
        # Read input
        print('Encrypting %s' % join('data/input', filename))
        print('           %s' % join('data/input', policy_filename))
        file = open(join('data/input', filename), 'rb')
        policy_file = open(join('data/input', policy_filename), 'r')
        read_policy = policy_file.readline()
        write_policy = policy_file.readline()
        # Encrypt a message
        create_record = user.create_record(read_policy, write_policy, file.read(), {'name': filename})
        file.close()
        # Send to insurance (this also stores the record)
        return user.send_create_record(create_record)

    def decrypt_file(self, user, location):
        """
        Decrypt the file with the given name (in /data/storage) and output it to /data/output
        :param user: The user to decrypt with
        :type user: scheme.user.User
        :param location: The location of the file to decrypt (in /data/storage)
        :return: The name of the output file (in /data/output)
        """
        # Give it to the user
        record = user.request_record(location)

        print('Decrypting %s' % join('data/storage', location))

        # print('Received record')
        # print(record.encryption_key_read)

        info, data = user.decrypt_record(record)

        print('Writing    %s' % join('data/output', info['name']))
        file = open(join('data/output', info['name']), 'wb')
        file.write(data)
        file.close()
        return info['name']

    def update_file(self, user, location):
        """
        Decrypt the file with the given name (in /data/storage) and output it to /data/output
        :param user: The user to decrypt with
        :type user: scheme.user.User
        :param location: The location of the file to decrypt (in /data/storage)
        :return: The name of the output file (in /data/output)
        """
        # Give it to the user
        record = user.request_record(location)
        print('Updating   %s' % join('data/storage', location))
        # Update the content
        update_record = user.update_record(record, b'updated content')
        # Send it to the insurance
        user.send_update_record(location, update_record)

    def run_encryptions(self):
        return list(map(lambda f: self.encrypt_file(self.bob, f),
                        [f for f in listdir('data/input') if
                         not f.endswith(".policy") and isfile(join('data/input', f))]))

    def run_updates(self, locations):
        list(map(lambda f: self.update_file(self.doctor, f), locations))

    def run_decryptions(self, locations):
        return list(map(lambda f: self.decrypt_file(self.doctor, f), locations))


if __name__ == '__main__':
    # RandomFileGenerator.clear()
    # RandomFileGenerator.generate(1024 * 1024, 10, debug=True)
    abe = ABEHealthCare()
    pr = cProfile.Profile()
    pr.runcall(abe.rw15)
    pr.print_stats(sort='cumtime')
