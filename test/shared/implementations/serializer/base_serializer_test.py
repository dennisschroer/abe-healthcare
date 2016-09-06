import unittest
from typing import List

from charm.toolbox.pairinggroup import PairingGroup
from shared.implementations.base_implementation import BaseImplementation
from shared.implementations.dacmacs13_implementation import DACMACS13Implementation
from shared.implementations.public_key.rsa_public_key import RSAPublicKey
from shared.implementations.rd13_implementation import RD13Implementation
from shared.implementations.rw15_implementation import RW15Implementation
from shared.implementations.serializer.base_serializer import BaseSerializer
from shared.implementations.taac12_implementation import TAAC12Implementation
from shared.model.global_parameters import GlobalParameters
from shared.model.records.data_record import DataRecord
from shared.utils.dict_utils import dict_equals_except_functions


class BaseSerializerTestCase(unittest.TestCase):
    def setUp(self):
        group = PairingGroup('SS512')
        public_key_scheme = RSAPublicKey()
        self.subject = BaseSerializer(group, public_key_scheme)
        self.implementations = [
            DACMACS13Implementation(),
            RD13Implementation(),
            RW15Implementation(),
            TAAC12Implementation()
        ]  # type: List[BaseImplementation]

    def test_replace_attributes(self):
        d = dict()  # type: dict
        a1 = self.subject.replace_attributes(d, 'ATTRIBUTE1')
        a2 = self.subject.replace_attributes(d, 'ATTRIBUTE2')
        a3 = self.subject.replace_attributes(d, 'ATTRIBUTE1')

        self.assertEqual(a1, a3)
        self.assertEqual('ATTRIBUTE1', self.subject.undo_attribute_replacement(d, a1))
        self.assertEqual('ATTRIBUTE2', self.subject.undo_attribute_replacement(d, a2))
        self.assertEqual('ATTRIBUTE1', self.subject.undo_attribute_replacement(d, a3))

    def test_serialize_deserialize_abe_ciphertext(self):
        for implementation in self.implementations:
            ciphertext = self._create_ciphertext(implementation)

            serializer = implementation.serializer
            serialized = serializer.serialize_abe_ciphertext(ciphertext)
            deserialized = serializer.deserialize_abe_ciphertext(serialized)

            self.assertEqual(ciphertext, deserialized)

    def test_serialize_deserialize_global_scheme_parameters(self):
        for implementation in self.implementations:
            self._setup_authorities(implementation)
            serialized = implementation.serializer.serialize_global_scheme_parameters(
                self.global_parameters.scheme_parameters)
            deserialized = implementation.serializer.deserialize_global_scheme_parameters(serialized)

            self.assertTrue(
                GlobalParameters.scheme_parameters_equal(self.global_parameters.scheme_parameters, deserialized))

    def test_serialize_deserialize_global_parameters(self):
        for implementation in self.implementations:
            self._setup_authorities(implementation)
            serialized = implementation.serializer.serialize_global_parameters(
                self.global_parameters)
            deserialized = implementation.serializer.deserialize_global_parameters(serialized)

            self.assertEqual(self.global_parameters, deserialized)

    def _setup_authorities(self, implementation: BaseImplementation) -> None:
        self.time_period = 1
        self.central_authority = implementation.create_central_authority()
        self.global_parameters = self.central_authority.central_setup()  # type: GlobalParameters
        self.attribute_authority = implementation.create_attribute_authority('A')
        self.attribute_authority.setup(self.central_authority, ['A@A', 'B@A'])
        self.public_keys = implementation.merge_public_keys(
            {'A': self.attribute_authority.public_keys(self.time_period)})

    def _create_ciphertext(self, implementation: BaseImplementation) -> bytes:
        self._setup_authorities(implementation)
        self.policy = 'A@A AND B@A'
        self.message, self.symmetric_key = implementation.generate_abe_key(self.global_parameters)
        ciphertext = implementation.abe_encrypt(self.global_parameters, self.public_keys, self.message, self.policy,
                                                self.time_period)
        return ciphertext

    def test_serialize_deserialize_data_record_meta(self):
        for implementation in self.implementations:
            serializer = implementation.serializer
            owner_keys = implementation.public_key_scheme.generate_key_pair(2048)
            write_keys = implementation.public_key_scheme.generate_key_pair(2048)

            ciphertext = self._create_ciphertext(implementation)

            data_record = DataRecord(
                read_policy='A@A AND B@A',
                write_policy='A@A AND B@A',
                owner_public_key=owner_keys.publickey(),
                write_public_key=write_keys.publickey(),
                encryption_key_read=ciphertext,
                encryption_key_owner=implementation.public_key_scheme.encrypt(self.symmetric_key, owner_keys),
                write_private_key=implementation.abe_encrypt_wrapped(self.global_parameters, self.public_keys,
                                                                     implementation.serializer.serialize_private_key(
                                                                         write_keys),
                                                                     self.policy, self.time_period),
                time_period=self.time_period,
                info=None,
                data=None
            )

            serialized = serializer.serialize_data_record_meta(data_record)
            deserialized = serializer.deserialize_data_record_meta(serialized)

            self.assertEqual(data_record.read_policy, deserialized.read_policy)
            self.assertEqual(data_record.write_policy, deserialized.write_policy)
            self.assertEqual(data_record.owner_public_key, deserialized.owner_public_key)
            self.assertEqual(data_record.write_public_key, deserialized.write_public_key)
            self.assertEqual(data_record.encryption_key_read, deserialized.encryption_key_read)
            self.assertEqual(data_record.encryption_key_owner, deserialized.encryption_key_owner)
            self.assertEqual(data_record.write_private_key, deserialized.write_private_key)
            self.assertEqual(data_record.time_period, deserialized.time_period)
            self.assertEqual(data_record.info, deserialized.info)
            self.assertEqual(data_record.data, deserialized.data)

    def test_serialize_deserialize_authority_public_keys(self):
        for implementation in self.implementations:
            self._setup_authorities(implementation)
            serialized = implementation.serializer.serialize_authority_public_keys(
                self.attribute_authority._public_keys)
            deserialized = implementation.serializer.deserialize_authority_public_keys(serialized)

            self.assertTrue(dict_equals_except_functions(self.attribute_authority._public_keys, deserialized))

    def test_serialize_deserialize_authority_secret_keys(self):
        for implementation in self.implementations:
            self._setup_authorities(implementation)
            serialized = implementation.serializer.serialize_authority_secret_keys(
                self.attribute_authority._secret_keys)
            deserialized = implementation.serializer.deserialize_authority_secret_keys(serialized)
            self.maxDiff = None
            self.assertEqual(self.attribute_authority._secret_keys, deserialized)

    def test_serialize_deserialize_keygen_request(self):
        for implementation in self.implementations:
            self._setup_authorities(implementation)
            request = {
                'gid': 'bob',
                'registration_data': self.central_authority.register_user('bob'),
                'attributes': ['ONE@A1', 'TWO@A1'],
                'time_period': 1
            }

            serialized = implementation.serializer.serialize_keygen_request(request)
            deserialized = implementation.serializer.deserialize_keygen_request(serialized)

            self.assertEqual(request, deserialized)

    def test_serialize_deserialize_user_secret_keys(self):
        for implementation in self.implementations:
            self._setup_authorities(implementation)

            registration_data = self.central_authority.register_user('bob')
            attributes = ['A@A', 'B@A']
            secret_keys = implementation.setup_secret_keys('bob')
            implementation.update_secret_keys(secret_keys,
                                              self.attribute_authority.keygen('bob', registration_data, attributes, 1))

            serialized = implementation.serializer.serialize_user_secret_keys(secret_keys)
            deserialized = implementation.serializer.deserialize_user_secret_keys(serialized)

            self.assertEqual(secret_keys, deserialized)

    def test_serialize_deserialize_registration_data(self):
        for implementation in self.implementations:
            self._setup_authorities(implementation)

            registration_data = self.central_authority.register_user('bob')
            serialized = implementation.serializer.serialize_registration_data(registration_data)
            deserialized = implementation.serializer.deserialize_registration_data(serialized)

            self.assertEqual(registration_data, deserialized)


if __name__ == '__main__':
    unittest.main()
