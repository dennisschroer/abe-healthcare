import unittest

from implementations.base_implementation import MockImplementation
from implementations.rw15 import RW15
from scheme.insurance_service import InsuranceService
from scheme.user import User
from scheme.user_client import UserClient


class UserClientTestCase(unittest.TestCase):
    def setUp(self):
        implementation = RW15()
        central_authority = implementation.create_central_authority()
        central_authority.setup()
        attribute_authority = implementation.create_attribute_authority('TEST')
        attribute_authority.setup(central_authority, ['TEST'])
        insurance_service = InsuranceService(central_authority.global_parameters, implementation)
        user = User('bob', implementation)
        user.issue_secret_keys(attribute_authority.keygen(user.gid, ['TEST']))
        self.subject = UserClient(user, insurance_service, implementation)

    def test_create_record(self):
        self.subject.user.owner_key_pair = self.subject.create_owner_key()
        create_record = self.subject.create_record('TEST@TEST', 'TEST@TEST', b'Hello world', {'test': 'info'})
        self.assertIsNotNone(create_record.data)
        self.assertNotEqual(create_record.data, b'Hello world')

        # Attempt to decrypt
        info, message = self.subject.decrypt_record(create_record)
        self.assertEqual(message, b'Hello world')
        self.assertEqual(info, {'test': 'info'})


if __name__ == '__main__':
    unittest.main()
