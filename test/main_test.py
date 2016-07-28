import unittest

from authority.attribute_authority import AttributeAuthority
from main import ABEHealthCare
from service.central_authority import CentralAuthority
from service.insurance_service import InsuranceService
from shared.implementations.rw15_implementation import RW15Implementation


class ABEHealthCareTestCase(unittest.TestCase):
    def setUp(self):
        self.subject = ABEHealthCare()

    def test_setup_central_authority_rw15(self):
        self.subject.implementation = RW15Implementation()

        self.assertIsNone(self.subject.central_authority)
        self.subject.setup_central_authority()
        self.assertIsNotNone(self.subject.central_authority)
        self.assertIsInstance(self.subject.central_authority, CentralAuthority)

    def test_setup_attribute_authorities_rw15(self):
        self.subject.implementation = RW15Implementation()
        self.subject.setup_central_authority()

        self.assertIsNone(self.subject.insurance_company)
        self.assertIsNone(self.subject.national_database)

        self.subject.setup_attribute_authorities(['ONE', 'TWO'], ['THREE', 'FOUR'])

        self.assertIsNotNone(self.subject.insurance_company)
        self.assertIsNotNone(self.subject.national_database)
        self.assertIsInstance(self.subject.insurance_company, AttributeAuthority)
        self.assertIsInstance(self.subject.national_database, AttributeAuthority)
        self.assertEqual(self.subject.insurance_company.name, 'INSURANCE')
        self.assertEqual(self.subject.national_database.name, 'NDB')

    def test_setup_service_rw15(self):
        self.subject.implementation = RW15Implementation()
        self.subject.setup_central_authority()
        self.subject.setup_attribute_authorities(['ONE', 'TWO'], ['THREE', 'FOUR'])

        self.assertIsNone(self.subject.insurance_service)
        self.subject.setup_service()
        self.assertIsNotNone(self.subject.insurance_service)
        self.assertIsInstance(self.subject.insurance_service, InsuranceService)
        self.assertEqual(len(self.subject.insurance_service.authorities), 2)
        self.assertIn('INSURANCE', self.subject.insurance_service.authorities)
        self.assertIn('NDB', self.subject.insurance_service.authorities)
        self.assertEqual(self.subject.insurance_company, self.subject.insurance_service.authorities['INSURANCE'])
        self.assertEqual(self.subject.national_database, self.subject.insurance_service.authorities['NDB'])


if __name__ == '__main__':
    unittest.main()
