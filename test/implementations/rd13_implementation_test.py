import unittest

from charm.toolbox.pairinggroup import PairingGroup
from implementations.rd13_implementation import RD13Implementation
from test.implementations.base_test import ImplementationBaseTestCase


class RD13ImplementationTestCase(ImplementationBaseTestCase, unittest.TestCase):
    def setUp(self):
        self.group = PairingGroup('SS512')
        self.subject = RD13Implementation(self.group)

    def test_ske_encrypt_decrypt(self):
        self.ske_encrypt_decrypt()

    def test_pke_sign_verify(self):
        self.pke_sign_verify()

    def test_encrypt_decrypt_abe(self):
        self.encrypt_decrypt_abe()

    def test_encrypt_decrypt_abe_wrapped(self):
        self.encrypt_decrypt_abe_wrapped()

    def test_abe_serialize_deserialize(self):
        self.abe_serialize_deserialize()


if __name__ == '__main__':
    unittest.main()