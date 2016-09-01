import unittest

from charm.toolbox.pairinggroup import PairingGroup
from shared.implementations.rw15_implementation import RW15Implementation
from test.shared.implementations.base_implementation_test import BaseImplementationTestCase


class RW15ImplementationTestCase(BaseImplementationTestCase):
    def setUp(self):
        self.group = PairingGroup('SS512')
        self.subject = RW15Implementation(self.group)

    def test_encrypt_decrypt_abe(self):
        self.encrypt_decrypt_abe()

    def test_encrypt_decrypt_abe_wrapped(self):
        self.encrypt_decrypt_abe_wrapped()

    def test_abe_serialize_deserialize(self):
        self.abe_serialize_deserialize()


if __name__ == '__main__':
    unittest.main()
