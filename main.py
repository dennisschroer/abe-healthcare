import cProfile
from os import listdir, path, makedirs
from os.path import isfile, join
from pstats import Stats

import psutil

from authority.attribute_authority import AttributeAuthority
from client.user_client import UserClient
from service.central_authority import CentralAuthority
from service.insurance_service import InsuranceService
from shared.connection.base_connection import BaseConnection
from shared.connection.user_insurance_connection import UserInsuranceConnection
from shared.implementations.base_implementation import BaseImplementation
from shared.implementations.dacmacs13_implementation import DACMACS13Implementation
from shared.implementations.rd13_implementation import RD13Implementation
from shared.implementations.rw15_implementation import RW15Implementation
from shared.implementations.taac12_implementation import TAAC12Implementation
from shared.model.user import User
from shared.serializer.pickle_serializer import PickleSerializer

from shared.utils.measure_util import connections_to_csv, pstats_to_csv

PROFILE_DATA_DIRECTORY = 'data/profile'


class ABEHealthCare(object):
    def __init__(self):
        self.implementation = None  # type: BaseImplementation
        self.central_authority = None  # type: CentralAuthority
        self.insurance_company = None  # type: AttributeAuthority
        self.national_database = None  # type: AttributeAuthority
        self.insurance_service = None  # type: InsuranceService
        self.doctor = None  # type: UserClient
        self.bob = None  # type: UserClient
        self.connections = list()  # type: List[BaseConnection]
        self.check_paths()

    def check_paths(self):
        if not path.exists('data/input'):
            makedirs('data/input')
        if not path.exists('data/storage'):
            makedirs('data/storage')
        if not path.exists('data/output'):
            makedirs('data/output')

    def rw15(self):
        self.implementation = RW15Implementation()
        self.run()

    def rd13(self):
        self.implementation = RD13Implementation()
        self.run()

    def taac12(self):
        self.implementation = TAAC12Implementation()
        self.run()

    def dacmacs13(self):
        self.implementation = DACMACS13Implementation()
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
        self.insurance_service = InsuranceService(PickleSerializer(self.implementation),
                                                  self.central_authority.global_parameters,
                                                  self.implementation.create_public_key_scheme())
        self.insurance_service.add_authority(self.insurance_company)
        self.insurance_service.add_authority(self.national_database)

    def create_user(self, name: str, insurance_attributes: list = None, national_attributes: list = None) -> UserClient:
        user = User(name, self.implementation)
        user.registration_data = self.central_authority.register_user(user.gid)

        serializer = PickleSerializer(self.implementation)
        connection = UserInsuranceConnection(self.insurance_service, serializer, benchmark=True)
        self.connections.append(connection)

        user_client = UserClient(user, connection, self.implementation)

        # Add attributes
        if insurance_attributes is not None:
            user.issue_secret_keys(
                self.insurance_company.keygen_valid_attributes(user.gid, user.registration_data, insurance_attributes,
                                                               1))
        if national_attributes is not None:
            user.issue_secret_keys(
                self.national_database.keygen_valid_attributes(user.gid, user.registration_data, national_attributes,
                                                               1))
        return user_client

    def setup(self):
        assert self.implementation is not None

        insurance_attributes = ['REVIEWER@INSURANCE', 'ADMINISTRATION@INSURANCE']
        national_attributes = ['DOCTOR@NDB', 'RADIOLOGIST@NDB']

        self.setup_central_authority()
        self.setup_attribute_authorities(insurance_attributes, national_attributes)
        self.setup_service()

        self.doctor = self.create_user('doctor', ['REVIEWER@INSURANCE', 'ADMINISTRATION@INSURANCE'], ['DOCTOR@NDB'])
        self.bob = self.create_user('bob', ['REVIEWER@INSURANCE'], ['DOCTOR@NDB'])

    def run_encryptions(self):
        return list(map(lambda f: self.bob.encrypt_file(f),
                        [f for f in listdir('data/input') if
                         not f.endswith(".policy") and isfile(join('data/input', f))]))

    def run_updates(self, locations):
        list(map(lambda f: self.doctor.update_file(f), locations))

    def run_policy_updates(self, locations):
        list(map(
            lambda f: self.bob.update_policy_file(f,
                                                  '(DOCTOR@NDB and REVIEWER@INSURANCE) or (RADIOLOGIST@NDB and REVIEWER@INSURANCE)',
                                                  'ADMINISTRATION@INSURANCE or (DOCTOR@NDB and REVIEWER@INSURANCE) or (RADIOLOGIST@NDB and REVIEWER@INSURANCE)',
                                                  1),
            locations))

    def run_decryptions(self, locations):
        return list(map(lambda f: self.doctor.decrypt_file(f), locations))

    def run(self):
        self.setup()
        locations = self.run_encryptions()
        # self.run_updates(locations)
        self.run_policy_updates(locations)
        self.run_decryptions(locations)

    def output_measurements(self, stats: Stats, connections):
        print("Times")
        stats.strip_dirs().sort_stats('cumtime').print_stats(
            '(user|authority|insurance|storage|RSA)')

        print("Network usage")
        for connection in connections:
            connection.dumps()
        connections.clear()


if __name__ == '__main__':
    abe = ABEHealthCare()
    pr = cProfile.Profile()

    if not path.exists(PROFILE_DATA_DIRECTORY):
        makedirs(PROFILE_DATA_DIRECTORY)

    process = psutil.Process()
    process.cpu_percent()

    print("== RW15 ((+) large attribute universe)")
    pr.runcall(abe.rw15)
    pr.dump_stats(path.join(PROFILE_DATA_DIRECTORY, 'rw15.txt'))
    stats = Stats(pr)
    abe.output_measurements(stats, abe.connections)
    pr.clear()
    print("CPU percent: %f" % process.cpu_percent())

    print("== RD13 ((+) fast decryption, (-) possible large ciphertext, (-) binary user tree)")
    pr.runcall(abe.rd13)
    pr.dump_stats(path.join(PROFILE_DATA_DIRECTORY, 'rd13.txt'))
    stats = Stats(pr)
    abe.output_measurements(stats, abe.connections)
    pr.clear()
    print("CPU percent: %f" % process.cpu_percent())

    print("== TAAC ((+) embedded timestamp)")
    pr.runcall(abe.taac12)
    pr.dump_stats(path.join(PROFILE_DATA_DIRECTORY, 'taac12.txt'))
    stats = Stats(pr)
    abe.output_measurements(stats, abe.connections)
    pr.clear()
    print("CPU percent: %f" % process.cpu_percent())

    print("== DACMACS ((+) outsourced decryption and/or re-encryption)")
    pr.runcall(abe.dacmacs13)

    # from pympler import muppy, summary
    # all_objects = muppy.get_objects()
    # sum1 = summary.summarize(all_objects)
    # summary.print_(sum1)

    pstats_to_csv(path.join(PROFILE_DATA_DIRECTORY, 'dacmacs.txt'), path.join(PROFILE_DATA_DIRECTORY, 'dacmacs.csv'))
    connections_to_csv(abe.connections, path.join(PROFILE_DATA_DIRECTORY, 'dacmacs_network.csv'))

    stats = Stats(pr)
    abe.output_measurements(stats, abe.connections)

    pr.clear()
    print("(INVALID, IS OVER ENTIRE PROCCESS) CPU percentage: %f" % process.cpu_percent())


