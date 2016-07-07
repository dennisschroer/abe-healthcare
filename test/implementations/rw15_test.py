import unittest

from charm.toolbox.pairinggroup import PairingGroup
from implementations.rw15 import RW15
from scheme.insurance_service import InsuranceService
from scheme.user import User


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.group = PairingGroup('SS512')
        self.subject = RW15(self.group)
    
    def test_encrypt_decrypt(self):
        # Setup authorities
        ca = self.subject.create_central_authority()
        ma1 = self.subject.create_attribute_authority('A1')
        ma2 = self.subject.create_attribute_authority('A2')
        global_parameters = ca.setup()
        ma1.setup(ca, ['ONE@A1', 'TWO@A1'])
        ma2.setup(ca, ['THREE@A2', 'FOUR@A2'])

        service = InsuranceService(global_parameters, self.subject)
        service.add_authority(ma1)
        service.add_authority(ma2)

        # Get secret keys
        user = User('bob', service, self.subject)
        sk = self.subject.setup_secret_keys(user)
        self.subject.update_secret_keys(sk, ma1.keygen(user, ['ONE@A1']))
        self.subject.update_secret_keys(sk, ma1.keygen(user, ['THREE@A2', 'FOUR@A2']))

        # Encrypt
        for m in ['Hello world']:
            c = self.subject.abe_encrypt(global_parameters, service.merge_public_keys(), 'Hello world', 'ONE@A1 AND THREE@A2')
            m2 = self.subject.abe_decrypt(global_parameters, sk, c)
            self.assertEqual(m, m2)

if __name__ == '__main__':
    unittest.main()
