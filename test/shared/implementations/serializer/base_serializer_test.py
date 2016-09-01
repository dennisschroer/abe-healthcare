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
from shared.model.records.data_record import DataRecord


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
            ciphertext = self._create_ciphertext(implementation,  b'Test message')

            serializer = implementation.serializer
            serialized = serializer.serialize_abe_ciphertext(ciphertext)
            deserialized = serializer.deserialize_abe_ciphertext(serialized)

            self.assertEqual(ciphertext, deserialized)

    def _create_ciphertext(self, implementation: BaseImplementation, message: bytes) -> bytes:
        time_period = 1
        central_authority = implementation.create_central_authority()
        global_parameters = central_authority.central_setup()
        attribute_authority = implementation.create_attribute_authority('A')
        attribute_authority.setup(central_authority, ['A@A', 'B@A'])
        public_keys = implementation.merge_public_keys({'A': attribute_authority.public_keys(time_period)})
        policy = 'A@A AND B@A'
        ciphertext = implementation.abe_encrypt(global_parameters, public_keys, message, policy, time_period)
        return ciphertext

    def test_serialize_deserialize_data_record_meta(self):
        for implementation in self.implementations:
            serializer = implementation.serializer
            owner_public, owner_private = implementation.public_key_scheme.generate_key_pair(2048)
            write_public, write_private = implementation.public_key_scheme.generate_key_pair(2048)

            time_period = 1
            central_authority = implementation.create_central_authority()
            global_parameters = central_authority.central_setup()
            attribute_authority = implementation.create_attribute_authority('A')
            attribute_authority.setup(central_authority, ['A@A', 'B@A'])
            public_keys = implementation.merge_public_keys({'A': attribute_authority.public_keys(time_period)})
            message = b'Test message'
            policy = 'A@A AND B@A'
            ciphertext = implementation.abe_encrypt(global_parameters, public_keys, message, policy, time_period)

            data_record = DataRecord(
                read_policy='A@A AND B@A',
                write_policy='A@A AND B@A',
                owner_public_key=owner_public,
                write_public_key=write_public,
                encryption_key_read=ciphertext,
                encryption_key_owner=implementation.public_key_scheme.encrypt(message, owner_private),
                write_private_key=implementation.abe_encrypt_wrapped(global_parameters, public_keys, write_private,
                                                                     policy, time_period),
                time_period=time_period,
                info=None,
                data=None
            )

            serialized = serializer.serialize_data_record_meta(data_record)
            deserialized = serializer.deserialize_data_record_meta(serialized)

            self.assertEqual(data_record, deserialized)


if __name__ == '__main__':
    unittest.main()
