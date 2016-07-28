import unittest

from charm.toolbox.pairinggroup import PairingGroup
from shared.implementations.dacmacs13_implementation import DACMACS13Implementation
from test.implementations.base_test import ImplementationBaseTestCase


class DACMACS13ImplementationTestCase(ImplementationBaseTestCase, unittest.TestCase):
    def setUp(self):
        self.group = PairingGroup('SS512')
        self.subject = DACMACS13Implementation(self.group)

    def test_encrypt_decrypt_abe(self):
        self.encrypt_decrypt_abe()

    def test_encrypt_decrypt_abe_wrapped(self):
        self.encrypt_decrypt_abe_wrapped()

    def test_abe_serialize_deserialize(self):
        self.abe_serialize_deserialize()


if __name__ == '__main__':
    unittest.main()
