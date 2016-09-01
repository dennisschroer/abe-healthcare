import unittest

from charm.toolbox.pairinggroup import PairingGroup
from shared.implementations.taac12_implementation import TAAC12Implementation
from test.shared.implementations import ImplementationBaseTestCase


class TAAC12ImplementationTestCase(ImplementationBaseTestCase, unittest.TestCase):
    def setUp(self):
        self.group = PairingGroup('SS512')
        self.subject = TAAC12Implementation(self.group)

    def test_encrypt_decrypt_abe(self):
        self.encrypt_decrypt_abe()

    def test_encrypt_decrypt_abe_wrapped(self):
        self.encrypt_decrypt_abe_wrapped()

    def test_abe_serialize_deserialize(self):
        self.abe_serialize_deserialize()


if __name__ == '__main__':
    unittest.main()
