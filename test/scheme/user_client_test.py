import unittest

from exception.policy_not_satisfied_exception import PolicyNotSatisfiedException
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
        attribute_authority.setup(central_authority, ['TEST@TEST', 'TEST2@TEST'])
        insurance_service = InsuranceService(central_authority.global_parameters, implementation)
        insurance_service.add_authority(attribute_authority)
        user = User('bob', implementation)
        user.issue_secret_keys(attribute_authority.keygen(user.gid, ['TEST@TEST']))
        self.subject = UserClient(user, insurance_service, implementation)

    def test_create_record(self):
        self.subject.user.owner_key_pair = self.subject.create_owner_key()
        create_record = self.subject.create_record('TEST@TEST', 'TEST@TEST', b'Hello world', {'test': 'info'})
        self.assertIsNotNone(create_record.info)
        self.assertIsNotNone(create_record.write_policy)
        self.assertIsNotNone(create_record.read_policy)
        self.assertIsNotNone(create_record.write_public_key)
        self.assertIsNotNone(create_record.owner_public_key)
        self.assertIsNotNone(create_record.encryption_key_read)
        self.assertIsNotNone(create_record.encryption_key_owner)
        self.assertIsNotNone(create_record.write_private_key)
        self.assertIsNotNone(create_record.data)
        self.assertNotEqual(create_record.data, b'Hello world')

        # Attempt to decrypt
        info, message = self.subject.decrypt_record(create_record)
        self.assertEqual(message, b'Hello world')
        self.assertEqual(info, {'test': 'info'})

    def test_decrypt_record(self):
        self.subject.user.owner_key_pair = self.subject.create_owner_key()
        create_record_valid = self.subject.create_record('TEST@TEST', 'TEST@TEST', b'Hello world', {'test': 'info'})
        create_record_invalid = self.subject.create_record('TEST2@TEST', 'TEST@TEST', b'Hello world', {'test': 'info'})

        # Attempt to decrypt
        info, message = self.subject.decrypt_record(create_record_valid)
        self.assertEqual(message, b'Hello world')
        self.assertEqual(info, {'test': 'info'})

        try:
            self.subject.decrypt_record(create_record_invalid)
            self.fail("PolicyNotSatisfiedException expected")
        except PolicyNotSatisfiedException:
            pass


if __name__ == '__main__':
    unittest.main()
