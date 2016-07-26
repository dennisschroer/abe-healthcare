import unittest

from implementations.public_key.base_public_key import BasePublicKey
from implementations.public_key.rsa_pke import RSAPublicKey
from test.data import lorem


class RSAPublicKeyTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subject = None  # type: BasePublicKey

    def setUp(self):
        self.subject = RSAPublicKey()

    def pke_sign_verify(self):
        key = self.subject.pke_generate_key_pair(1024)
        for m in [b'Hello world', lorem]:
            s = self.subject.pke_sign(key, m)
            self.assertNotEqual(s, m)
            self.assertTrue(self.subject.pke_verify(key, s, m))


if __name__ == '__main__':
    unittest.main()
