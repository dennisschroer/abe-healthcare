import unittest

from shared.implementations.symmetric_key.aes_symmetric_key import AESSymmetricKey
from shared.implementations.symmetric_key.base_symmetric_key import BaseSymmetricKey
from test.data import lorem


class AESSymmetricKeyTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subject = None  # type: BaseSymmetricKey

    def setUp(self):
        self.subject = AESSymmetricKey()

    def ske_encrypt_decrypt(self):
        key = b'a' * self.subject.ske_key_size()
        for m in [b'Hello world', lorem]:
            c = self.subject.ske_encrypt(m, key)
            self.assertNotEqual(c, m)
            d = self.subject.ske_decrypt(c, key)
            self.assertEqual(m, d)
            r = self.subject.ske_decrypt(c, b'b' * self.subject.ske_key_size())
            self.assertNotEqual(m, r)


if __name__ == '__main__':
    unittest.main()
