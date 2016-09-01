import unittest

from charm.core.math.pairing import GT
from shared.exception.policy_not_satisfied_exception import PolicyNotSatisfiedException
from shared.implementations.base_implementation import BaseImplementation
from test.data import lorem


class BaseImplementationTestCase(unittest.TestCase):
    # noinspection PyUnusedLocal,PyPep8Naming
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subject = None  # type: BaseImplementation

    def setup_abe(self):
        # Setup authorities
        self.ca = self.subject.create_central_authority()
        self.ma1 = self.subject.create_attribute_authority('A1')
        self.ma2 = self.subject.create_attribute_authority('A2')
        self.global_parameters = self.ca.central_setup()
        self.ma1.setup(self.ca, ['ONE@A1', 'TWO@A1'])
        self.ma2.setup(self.ca, ['THREE@A2', 'FOUR@A2'])

        self.registration_data = self.ca.register_user('alice')

        # Setup keys
        self.public_keys = self.subject.merge_public_keys({
            self.ma1.name: self.ma1.public_keys(1),
            self.ma2.name: self.ma2.public_keys(1)
        })
        self.valid_secret_keys = []  # type: list
        self.invalid_secret_keys = []  # type:list

        # Just enough secret keys
        self.secret_keys = self.subject.setup_secret_keys('alice')
        self.registration_data = self.ca.register_user('alice')
        self.subject.update_secret_keys(self.secret_keys,
                                        self.ma1.keygen('alice', self.registration_data, ['ONE@A1'], 1))
        self.subject.update_secret_keys(self.secret_keys,
                                        self.ma2.keygen('alice', self.registration_data, ['THREE@A2'], 1))
        self.valid_secret_keys.append(self.secret_keys)

        # All secret keys
        self.all_secret_keys = self.subject.setup_secret_keys('alice')
        self.subject.update_secret_keys(self.all_secret_keys,
                                        self.ma1.keygen('alice', self.registration_data, ['ONE@A1', 'TWO@A1'], 1))
        self.subject.update_secret_keys(self.all_secret_keys,
                                        self.ma2.keygen('alice', self.registration_data, ['THREE@A2', 'FOUR@A2'], 1))
        self.valid_secret_keys.append(self.all_secret_keys)

        # No secret keys
        self.invalid_secret_keys.append(self.subject.setup_secret_keys('alice'))

        # Not enough secret keys
        self.not_enough_secret_keys = self.subject.setup_secret_keys('alice')
        self.subject.update_secret_keys(self.not_enough_secret_keys,
                                        self.ma1.keygen('alice', self.registration_data, ['ONE@A1'], 1))
        self.invalid_secret_keys.append(self.not_enough_secret_keys)

        # All secret keys, but invalid time period
        self.invalid_time_keys = self.subject.setup_secret_keys('alice')
        self.subject.update_secret_keys(self.invalid_time_keys,
                                        self.ma1.keygen('alice', self.registration_data, ['ONE@A1', 'TWO@A1'], 2))
        self.subject.update_secret_keys(self.invalid_time_keys,
                                        self.ma2.keygen('alice', self.registration_data, ['THREE@A2', 'FOUR@A2'], 2))

        self.policy = '(ONE@A1 AND THREE@A2) OR (ONE@A1 AND TWO@A1 AND FOUR@A2) OR (ONE@A1 AND THREE@A2 AND FOUR@A2)'

    def encrypt_decrypt_abe(self):
        self.setup_abe()

        m = self.global_parameters.group.random(GT)

        # Encrypt message
        ciphertext = self.subject.abe_encrypt(self.global_parameters, self.public_keys, m, self.policy, 1)
        self.assertNotEqual(m, ciphertext)

        # if self.subject.decryption_keys_required:
        #    decryption_keys = self.subject.decryption_keys()

        # Attempt to decrypt
        for secret_keys in self.valid_secret_keys:
            decryption_keys = self.subject.decryption_keys(self.global_parameters,
                                                           {self.ma1.name: self.ma1, self.ma2.name: self.ma2},
                                                           secret_keys, self.registration_data, ciphertext, 1
                                                           )
            decrypted = self.subject.abe_decrypt(self.global_parameters,
                                                 decryption_keys, 'alice',
                                                 ciphertext, self.registration_data)
            self.assertEqual(m, decrypted)

        for secret_keys in self.invalid_secret_keys:
            try:
                decryption_keys = self.subject.decryption_keys(self.global_parameters,
                                                               {self.ma1.name: self.ma1, self.ma2.name: self.ma2},
                                                               secret_keys, self.registration_data, ciphertext, 1
                                                               )
                self.subject.abe_decrypt(self.global_parameters, decryption_keys,
                                         'alice', ciphertext, self.registration_data)
                self.fail("Should throw an PolicyNotSatisfiedException because of insufficient secret keys")
            except PolicyNotSatisfiedException:
                pass

        try:
            decryption_keys = self.subject.decryption_keys(self.global_parameters,
                                                           {self.ma1.name: self.ma1, self.ma2.name: self.ma2},
                                                           self.invalid_time_keys, self.registration_data, ciphertext, 2
                                                           )
            self.subject.abe_decrypt(self.global_parameters, decryption_keys,
                                     'alice', ciphertext, self.registration_data)
            self.fail("Should throw an PolicyNotSatisfiedException because of insufficient secret keys")
        except PolicyNotSatisfiedException:
            pass

    def encrypt_decrypt_abe_wrapped(self):
        self.setup_abe()

        for m in [b'Hello world', lorem]:
            # Encrypt message
            key, ciphertext = self.subject.abe_encrypt_wrapped(self.global_parameters, self.public_keys, m, self.policy,
                                                               1)
            self.assertNotEqual(m, ciphertext)

            # Attempt to decrypt the messages
            for secret_keys in self.valid_secret_keys:
                decryption_keys = self.subject.decryption_keys(self.global_parameters,
                                                               {self.ma1.name: self.ma1, self.ma2.name: self.ma2},
                                                               secret_keys, self.registration_data,
                                                               key, 1
                                                               )
                decrypted = self.subject.abe_decrypt_wrapped(self.global_parameters,
                                                             decryption_keys, 'alice',
                                                             (key, ciphertext), self.registration_data)
                self.assertEqual(m, decrypted)

            for secret_keys in self.invalid_secret_keys:
                try:
                    decryption_keys = self.subject.decryption_keys(self.global_parameters,
                                                                   {self.ma1.name: self.ma1, self.ma2.name: self.ma2},
                                                                   secret_keys, self.registration_data,
                                                                   key, 1
                                                                   )
                    self.subject.abe_decrypt_wrapped(self.global_parameters,
                                                     decryption_keys,
                                                     'alice', (key, ciphertext), self.registration_data)
                    self.fail("Should throw an PolicyNotSatisfiedException because of insufficient secret keys")
                except PolicyNotSatisfiedException:
                    pass

            try:
                decryption_keys = self.subject.decryption_keys(self.global_parameters,
                                                               {self.ma1.name: self.ma1, self.ma2.name: self.ma2},
                                                               self.invalid_time_keys, self.registration_data,
                                                               key, 2
                                                               )
                self.subject.abe_decrypt_wrapped(self.global_parameters,
                                                 decryption_keys,
                                                 'alice', (key, ciphertext), self.registration_data)
                self.fail("Should throw an PolicyNotSatisfiedException because of insufficient secret keys")
            except PolicyNotSatisfiedException:
                pass

    def abe_serialize_deserialize(self):
        self.setup_abe()

        m = self.global_parameters.group.random(GT)

        # Encrypt message
        ciphertext = self.subject.abe_encrypt(self.global_parameters, self.public_keys, m, self.policy, 1)

        serializer = self.subject.serializer

        serialized = serializer.serialize_abe_ciphertext(ciphertext)
        self.assertIsNotNone(serialized)

        deserialized = serializer.deserialize_abe_ciphertext(serialized)
        self.assertIsNotNone(deserialized)
        self.assertEqual(deserialized, ciphertext)


if __name__ == '__main__':
    unittest.main()
