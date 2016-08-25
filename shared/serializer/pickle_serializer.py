import pickle
from typing import Dict

from authority.attribute_authority import AttributeAuthority
from shared.implementations.base_implementation import BaseImplementation
from shared.implementations.public_key.base_public_key import BasePublicKey
from shared.model.global_parameters import GlobalParameters
from shared.model.records.create_record import CreateRecord
from shared.model.records.data_record import DataRecord
from shared.model.records.policy_update_record import PolicyUpdateRecord
from shared.model.records.update_record import UpdateRecord

DATA_RECORD_READ_POLICY = 'rp'
DATA_RECORD_WRITE_POLICY = 'wp'
DATA_RECORD_OWNER_PUBLIC_KEY = 'opk'
DATA_RECORD_WRITE_PUBLIC_KEY = 'wpk'
DATA_RECORD_ENCRYPTION_KEY_READ = 'ekr'
DATA_RECORD_ENCRYPTION_KEY_OWNER = 'eko'
DATA_RECORD_WRITE_SECRET_KEY = 'wsk'
DATA_RECORD_INFO = 'i'
DATA_RECORD_TIME_PERIOD = 't'
DATA_RECORD_SIGNATURE = 's'


class PickleSerializer(object):
    def __init__(self, implementation: BaseImplementation) -> None:
        self.implementation = implementation

    def global_parameters(self, global_parameters: GlobalParameters) -> bytes:
        return pickle.dumps({
            'group': global_parameters.group.param,
            'scheme': self.implementation.create_serializer().serialize_global_scheme_parameters(
                global_parameters.scheme_parameters)
        })

    def data_record(self, data_record: DataRecord) -> bytes:
        return pickle.dumps({
            'meta': self.serialize_data_record_meta(data_record),
            'data': data_record.data
        })

    def authorities(self, response: Dict[str, AttributeAuthority]) -> bytes:
        return pickle.dumps({
                                n: {'name': a.name, 'attributes': a.attributes} for n, a in response.items()
                                })

    def create_record(self, create_record: CreateRecord) -> bytes:
        return pickle.dumps({
            'meta': self.serialize_data_record_meta(create_record),
            'data': create_record.data
        })

    def update_record(self, update_record: UpdateRecord) -> bytes:
        return pickle.dumps({
            'signature': update_record.signature,
            'data': update_record.data
        })

    def policy_update_record(self, policy_update_record: PolicyUpdateRecord) -> bytes:
        return pickle.dumps({
            'meta': self.policy_update_record_meta(policy_update_record),
            'data': policy_update_record.data
        })

    def policy_update_record_meta(self, policy_update_record: PolicyUpdateRecord) -> bytes:
        """
        Serialize the meta of a PolicyUpdateRecord
        :param policy_update_record:
        :return:
        """
        return pickle.dumps({
            DATA_RECORD_READ_POLICY: policy_update_record.read_policy,
            DATA_RECORD_WRITE_POLICY: policy_update_record.write_policy,
            DATA_RECORD_WRITE_PUBLIC_KEY: self.implementation.create_public_key_scheme().export_key(
                policy_update_record.write_public_key),
            DATA_RECORD_ENCRYPTION_KEY_READ: self.implementation.create_serializer().serialize_abe_ciphertext(
                policy_update_record.encryption_key_read),
            DATA_RECORD_ENCRYPTION_KEY_OWNER: policy_update_record.encryption_key_owner,
            DATA_RECORD_TIME_PERIOD: policy_update_record.time_period,
            DATA_RECORD_INFO: policy_update_record.info,
            DATA_RECORD_WRITE_SECRET_KEY: (
                self.implementation.create_serializer().serialize_abe_ciphertext(
                    policy_update_record.write_private_key[0]),
                policy_update_record.write_private_key[1]),
            DATA_RECORD_SIGNATURE: policy_update_record.signature,
        })

    def serialize_data_record_meta(self, data_record: DataRecord) -> bytes:
        """
        Serialize a data record
        :param data_record:
        :return:
        """
        public_key_scheme = self.implementation.create_public_key_scheme()
        return pickle.dumps({
            DATA_RECORD_READ_POLICY: data_record.read_policy,
            DATA_RECORD_WRITE_POLICY: data_record.write_policy,
            DATA_RECORD_OWNER_PUBLIC_KEY: public_key_scheme.export_key(data_record.owner_public_key),
            DATA_RECORD_WRITE_PUBLIC_KEY: public_key_scheme.export_key(data_record.write_public_key),
            DATA_RECORD_ENCRYPTION_KEY_READ: self.implementation.create_serializer().serialize_abe_ciphertext(
                data_record.encryption_key_read),
            DATA_RECORD_ENCRYPTION_KEY_OWNER: data_record.encryption_key_owner,
            DATA_RECORD_TIME_PERIOD: data_record.time_period,
            DATA_RECORD_INFO: data_record.info,
            DATA_RECORD_WRITE_SECRET_KEY: (
                self.implementation.create_serializer().serialize_abe_ciphertext(data_record.write_private_key[0]),
                data_record.write_private_key[1])
        })

    def deserialize_data_record_meta(self, byte_object: bytes) -> DataRecord:
        """

        :param byte_object:
        :return:
        """
        public_key_scheme = self.implementation.create_public_key_scheme()
        d = pickle.loads(byte_object)
        return DataRecord(
            read_policy=d[DATA_RECORD_READ_POLICY],
            write_policy=d[DATA_RECORD_WRITE_POLICY],
            owner_public_key=public_key_scheme.import_key(d[DATA_RECORD_OWNER_PUBLIC_KEY]),
            write_public_key=public_key_scheme.import_key(d[DATA_RECORD_WRITE_PUBLIC_KEY]),
            encryption_key_read=self.implementation.create_serializer().deserialize_abe_ciphertext(
                d[DATA_RECORD_ENCRYPTION_KEY_READ]),
            encryption_key_owner=d[DATA_RECORD_ENCRYPTION_KEY_OWNER],
            write_private_key=(
            self.implementation.create_serializer().deserialize_abe_ciphertext(d[DATA_RECORD_WRITE_SECRET_KEY][0]),
            d[DATA_RECORD_WRITE_SECRET_KEY][1]),
            time_period=d[DATA_RECORD_TIME_PERIOD],
            info=d[DATA_RECORD_INFO],
            data=None
        )

    def public_keys(self, public_keys) -> bytes:
        return pickle.dumps(public_keys)

    def keygen(self, request) -> bytes:
        return pickle.dumps(request)

    def secret_keys(self, secret_keys) -> bytes:
        return pickle.dumps(secret_keys)