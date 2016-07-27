import pickle
import unittest
from typing import List

from client.user_client import UserClient
from exception.policy_not_satisfied_exception import PolicyNotSatisfiedException
from implementations.base_implementation import BaseImplementation
from implementations.dacmacs13_implementation import DACMACS13Implementation
from implementations.rd13_implementation import RD13Implementation
from implementations.rw15_implementation import RW15Implementation
from implementations.taac12_implementation import TAAC12Implementation
from model.user import User
from service.insurance_service import InsuranceService


class UserClientTestCase(unittest.TestCase):
    def setUp(self):
        self.implementations = [RW15Implementation(), DACMACS13Implementation(), RD13Implementation(),
                                TAAC12Implementation()]  # type: List[BaseImplementation]

    def setUpWithImplementation(self, implementation: BaseImplementation):
        central_authority = implementation.create_central_authority()
        central_authority.setup()
        attribute_authority = implementation.create_attribute_authority('TEST')
        attribute_authority.setup(central_authority, ['TEST@TEST', 'TEST2@TEST', 'TEST3@TEST', 'TEST4@TEST'])
        insurance_service = InsuranceService(central_authority.global_parameters, implementation)
        insurance_service.add_authority(attribute_authority)
        user = User('bob', implementation)
        central_authority.register_user(user.gid)
        user.issue_secret_keys(
            attribute_authority.keygen(user.gid, user.registration_data, ['TEST@TEST', 'TEST3@TEST', 'TEST4@TEST'], 1))
        self.subject = UserClient(user, insurance_service, implementation)

    def test_create_record(self):
        for implementation in self.implementations:
            self.setUpWithImplementation(implementation)
            self._test_create_record()

    def _test_create_record(self):
        self.subject.user.owner_key_pair = self.subject.create_owner_key()
        create_record = self.subject.create_record('TEST@TEST', 'TEST@TEST', b'Hello world', {'test': 'info'}, 1)
        self.assertIsNotNone(create_record.info)
        self.assertIsNotNone(create_record.write_policy)
        self.assertIsNotNone(create_record.read_policy)
        self.assertIsNotNone(create_record.write_public_key)
        self.assertIsNotNone(create_record.owner_public_key)
        self.assertIsNotNone(create_record.encryption_key_read)
        self.assertIsNotNone(create_record.encryption_key_owner)
        self.assertIsNotNone(create_record.write_private_key)
        self.assertIsNotNone(create_record.time_period)
        self.assertIsNotNone(create_record.data)
        self.assertNotEqual(create_record.data, b'Hello world')

        # Attempt to decrypt
        info, message = self.subject.decrypt_record(create_record)
        self.assertEqual(message, b'Hello world')
        self.assertEqual(info, {'test': 'info'})

    def test_update_record(self):
        for implementation in self.implementations:
            self.setUpWithImplementation(implementation)
            self._test_update_record()

    def _test_update_record(self):
        self.subject.user.owner_key_pair = self.subject.create_owner_key()
        create_record = self.subject.create_record('TEST@TEST', 'TEST@TEST', b'Hello world', {'test': 'info'}, 1)
        update_record = self.subject.update_record(create_record, b'Goodbye world')
        self.assertIsNotNone(update_record.data)
        self.assertIsNotNone(update_record.signature)
        pke = self.subject.implementation.create_public_key_scheme()
        self.assertTrue(pke.verify(create_record.write_public_key, update_record.signature,
                                   update_record.data))

        # Update the original record
        create_record.update(update_record)

        # Attempt to decrypt
        info, message = self.subject.decrypt_record(create_record)
        self.assertEqual(message, b'Goodbye world')

    def test_update_policy(self):
        for implementation in self.implementations:
            self.setUpWithImplementation(implementation)
            self._test_update_policy()

    def _test_update_policy(self):
        self.subject.user.owner_key_pair = self.subject.create_owner_key()
        create_record = self.subject.create_record('TEST@TEST', 'TEST@TEST', b'Hello world', {'test': 'info'}, 1)
        update_record = self.subject.update_policy(create_record, 'TEST3@TEST', 'TEST4@TEST', 1)

        self.assertIsNotNone(update_record.info)
        self.assertIsNotNone(update_record.write_policy)
        self.assertIsNotNone(update_record.read_policy)
        self.assertIsNotNone(update_record.write_public_key)
        self.assertIsNotNone(update_record.encryption_key_read)
        self.assertIsNotNone(update_record.encryption_key_owner)
        self.assertIsNotNone(update_record.write_private_key)
        self.assertIsNotNone(update_record.time_period)
        self.assertIsNotNone(update_record.data)
        self.assertIsNotNone(update_record.signature)
        pke = self.subject.implementation.create_public_key_scheme()
        self.assertTrue(pke.verify(create_record.owner_public_key, update_record.signature,
                                   pickle.dumps((update_record.read_policy,
                                                 update_record.write_policy,
                                                 update_record.time_period))))

        # Update the original record
        create_record.update_policy(update_record)

        self.assertEqual('TEST3@TEST', create_record.read_policy)
        self.assertEqual('TEST4@TEST', create_record.write_policy)

        # Attempt to decrypt
        info, message = self.subject.decrypt_record(create_record)
        self.assertEqual(message, b'Hello world')

    def test_update_policy_insufficient_policy(self):
        for implementation in self.implementations:
            self.setUpWithImplementation(implementation)
            self._test_update_policy_insufficient_policy()

    def _test_update_policy_insufficient_policy(self):
        self.subject.user.owner_key_pair = self.subject.create_owner_key()
        create_record = self.subject.create_record('TEST@TEST', 'TEST@TEST', b'Hello world', {'test': 'info'}, 1)

        # Now update to policies which the user can not satisfy
        update_record = self.subject.update_policy(create_record, 'TEST2@TEST', 'TEST2@TEST', 1)

        # Update the original record
        create_record.update_policy(update_record)

        self.assertEqual('TEST2@TEST', create_record.read_policy)
        self.assertEqual('TEST2@TEST', create_record.write_policy)

        # Attempt to decrypt
        try:
            self.subject.decrypt_record(create_record)
            self.fail('PolicyNotSatisfiedException expected')
        except PolicyNotSatisfiedException:
            pass

    def test_update_policy_invalid_timeperiod(self):
        for implementation in self.implementations:
            self.setUpWithImplementation(implementation)
            self._test_update_policy_invalid_timeperiod()

    def _test_update_policy_invalid_timeperiod(self):
        self.subject.user.owner_key_pair = self.subject.create_owner_key()
        create_record = self.subject.create_record('TEST@TEST', 'TEST@TEST', b'Hello world', {'test': 'info'}, 1)

        # Now update to policies which the user can not satisfy
        update_record = self.subject.update_policy(create_record, create_record.read_policy, create_record.write_policy,
                                                   2)

        # Update the original record
        create_record.update_policy(update_record)

        self.assertEqual('TEST@TEST', create_record.read_policy)
        self.assertEqual('TEST@TEST', create_record.write_policy)

        # Attempt to decrypt
        try:
            self.subject.decrypt_record(create_record)
            self.fail('PolicyNotSatisfiedException expected')
        except PolicyNotSatisfiedException:
            pass

    def test_decrypt_record(self):
        for implementation in self.implementations:
            self.setUpWithImplementation(implementation)
            self._test_decrypt_record()

    def _test_decrypt_record(self):
        self.subject.user.owner_key_pair = self.subject.create_owner_key()
        create_record_valid = self.subject.create_record('TEST@TEST', 'TEST@TEST', b'Hello world', {'test': 'info'}, 1)

        # Attempt to decrypt
        info, message = self.subject.decrypt_record(create_record_valid)
        self.assertEqual(message, b'Hello world')
        self.assertEqual(info, {'test': 'info'})

    def test_decrypt_record_insufficient_attributes(self):
        for implementation in self.implementations:
            self.setUpWithImplementation(implementation)
            self._test_decrypt_record_insufficient_attributes()

    def _test_decrypt_record_insufficient_attributes(self):
        self.subject.user.owner_key_pair = self.subject.create_owner_key()
        create_record_invalid = self.subject.create_record('TEST2@TEST', 'TEST@TEST', b'Hello world', {'test': 'info'},
                                                           1)

        # Attempt to decrypt
        try:
            self.subject.decrypt_record(create_record_invalid)
            self.fail("PolicyNotSatisfiedException expected")
        except PolicyNotSatisfiedException:
            pass

    def test_decrypt_record_invalid_time_period(self):
        for implementation in self.implementations:
            self.setUpWithImplementation(implementation)
            self._test_decrypt_record_invalid_time_period()

    def _test_decrypt_record_invalid_time_period(self):
        self.subject.user.owner_key_pair = self.subject.create_owner_key()
        create_record_invalid = self.subject.create_record('TEST@TEST', 'TEST@TEST', b'Hello world', {'test': 'info'},
                                                           2)

        # Attempt to decrypt
        try:
            self.subject.decrypt_record(create_record_invalid)
            self.fail("PolicyNotSatisfiedException expected")
        except PolicyNotSatisfiedException:
            pass


if __name__ == '__main__':
    unittest.main()
