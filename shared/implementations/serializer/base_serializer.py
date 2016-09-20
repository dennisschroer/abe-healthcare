import pickle
import sys
from pickle import Unpickler
from typing import Any

from charm.toolbox.pairinggroup import PairingGroup
from shared.model.types import AbeEncryption, SecretKeyStore, AuthorityPublicKeysStore, AuthoritySecretKeysStore

PY3 = (sys.hexversion >= 0x30000f0)
if PY3:
    from io import BytesIO as StringIO
else:
    from StringIO import StringIO
from pickle import Pickler
from typing import Dict

import charm
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


class BaseSerializer(object):
    def __init__(self, group: PairingGroup, public_key_scheme) -> None:
        self.group = group
        self.public_key_scheme = public_key_scheme

    def serialize_abe_ciphertext(self, ciphertext: AbeEncryption) -> Any:
        """
        Serialize the ciphertext resulting form an attribute based encryption to an object which can be pickled.

        This is required because by default, instances of pairing.Element can not be pickled but have to be serialized.
        :return: An object, probably a dict, which can be pickled
        """
        raise NotImplementedError()

    def deserialize_abe_ciphertext(self, dictionary: Any) -> AbeEncryption:
        """
        Deserialize a (pickleable) dictionary back to a (non-pickleable) ciphertext.

        :return: The deserialized ciphertext.
        """
        raise NotImplementedError()

    def serialize_global_scheme_parameters(self, scheme_parameters):
        raise NotImplementedError()

    def deserialize_global_scheme_parameters(self, scheme_parameters):
        raise NotImplementedError()

    def serialize_global_parameters(self, global_parameters: GlobalParameters) -> bytes:
        return pickle.dumps({
            'group': global_parameters.group.param,
            'scheme': self.serialize_global_scheme_parameters(
                global_parameters.scheme_parameters)
        })

    def deserialize_global_parameters(self, data: bytes) -> GlobalParameters:
        unpickled = pickle.loads(data)
        return GlobalParameters(
            PairingGroup(unpickled['group']),
            self.deserialize_global_scheme_parameters(unpickled['scheme'])
        )

    @staticmethod
    def replace_attributes(dict: dict, keyword: str) -> int:
        """
        Determine a shorter identifier for the given keyword, and store it in the dict. If a keyword is already
        in the dictionary, the existing replacement identifier is used.
        :param dict: The dictionary with existing replacements.
        :param keyword: The keyword to replace.
        :return: int The replacement keyword. The dict is also updated.

        >>> d = dict()
        >>> a = BaseSerializer.replace_attributes(d, 'TEST123')
        >>> b = BaseSerializer.replace_attributes(d, 'TEST123')
        >>> c = BaseSerializer.replace_attributes(d, 'TEST')
        >>> a == b
        True
        >>> b == c
        False
        >>> d[a]
        'TEST123'
        >>> d[b]
        'TEST123'
        >>> d[c]
        'TEST'
        """
        for (key, value) in dict.items():
            if value == keyword:
                # Already in the dictionary
                return key
        # Not in dict
        key = len(dict)
        dict[key] = keyword
        return key

    @staticmethod
    def undo_attribute_replacement(dict: dict, replacement: int) -> str:
        """
        Undo the attribute replacement as result from the attribute replacement.
        :param dict: The dictionary with the replacements.
        :param replacement: The replacement to revert to the original keyword.
        :return: The original keyword.

        >>> d = dict()
        >>> a = BaseSerializer.replace_attributes(d, 'TEST123')
        >>> b = BaseSerializer.replace_attributes(d, 'TEST')
        >>> BaseSerializer.undo_attribute_replacement(d, a) == 'TEST123'
        True
        >>> BaseSerializer.undo_attribute_replacement(d, b) == 'TEST'
        True
        >>> BaseSerializer.undo_attribute_replacement(d, 123)
        Traceback (most recent call last):
        ...
        KeyError: 123
        """
        return dict[replacement]

    def serialize_data_record(self, data_record: DataRecord) -> bytes:
        return pickle.dumps({
            'meta': self.serialize_data_record_meta(data_record),
            'data': data_record.data
        })

    # noinspection PyMethodMayBeStatic
    def serialize_authorities(self, response: Dict[str, Any]) -> bytes:
        return pickle.dumps({
                                n: {'name': a.name, 'attributes': a.attributes} for n, a in response.items()
                                })

    def serialize_create_record(self, create_record: CreateRecord) -> bytes:
        return pickle.dumps({
            'meta': self.serialize_data_record_meta(create_record),
            'data': create_record.data
        })

    def serialize_update_record(self, update_record: UpdateRecord) -> bytes:
        return self.dumps(update_record)

    def serialize_policy_update_record(self, policy_update_record: PolicyUpdateRecord) -> bytes:
        return pickle.dumps({
            'meta': self.serialize_policy_update_record_meta(policy_update_record),
            'data': policy_update_record.data
        })

    def serialize_policy_update_record_meta(self, policy_update_record: PolicyUpdateRecord) -> bytes:
        """
        Serialize the meta of a PolicyUpdateRecord
        :param policy_update_record:
        :return:
        """
        return pickle.dumps({
            DATA_RECORD_READ_POLICY: policy_update_record.read_policy,
            DATA_RECORD_WRITE_POLICY: policy_update_record.write_policy,
            DATA_RECORD_WRITE_PUBLIC_KEY: self.serialize_public_key(
                policy_update_record.write_public_key),
            DATA_RECORD_ENCRYPTION_KEY_READ: self.serialize_abe_ciphertext(
                policy_update_record.encryption_key_read),
            DATA_RECORD_ENCRYPTION_KEY_OWNER: policy_update_record.encryption_key_owner,
            DATA_RECORD_TIME_PERIOD: policy_update_record.time_period,
            DATA_RECORD_INFO: policy_update_record.info,
            DATA_RECORD_WRITE_SECRET_KEY: (
                self.serialize_abe_ciphertext(
                    policy_update_record.write_private_key[0]),
                policy_update_record.write_private_key[1]),
            DATA_RECORD_SIGNATURE: policy_update_record.signature,
        })

    def serialize_public_key(self, public_key) -> bytes:
        return self.public_key_scheme.export_key(public_key)

    def serialize_private_key(self, private_key):
        return self.public_key_scheme.export_key(private_key)

    def deserialize_public_key(self, data: bytes):
        return self.public_key_scheme.import_key(data)

    def serialize_data_record_meta(self, data_record: DataRecord) -> bytes:
        """
        Serialize a data record
        :param data_record:
        :return:
        """
        return pickle.dumps({
            DATA_RECORD_READ_POLICY: data_record.read_policy,
            DATA_RECORD_WRITE_POLICY: data_record.write_policy,
            DATA_RECORD_OWNER_PUBLIC_KEY: self.serialize_public_key(data_record.owner_public_key),
            DATA_RECORD_WRITE_PUBLIC_KEY: self.serialize_public_key(data_record.write_public_key),
            DATA_RECORD_ENCRYPTION_KEY_READ: self.serialize_abe_ciphertext(
                data_record.encryption_key_read),
            DATA_RECORD_ENCRYPTION_KEY_OWNER: data_record.encryption_key_owner,
            DATA_RECORD_TIME_PERIOD: data_record.time_period,
            DATA_RECORD_INFO: data_record.info,
            DATA_RECORD_WRITE_SECRET_KEY: (
                self.serialize_abe_ciphertext(data_record.write_private_key[0]),
                data_record.write_private_key[1])
        })

    def deserialize_data_record_meta(self, byte_object: bytes) -> DataRecord:
        """
        Deserialize de meta of a data record in a DataRecord instance.
        The data property of the DataRecord is None.
        :param byte_object: The data to deserialize.
        :return: An instance of the DataRecord class.
        """
        d = pickle.loads(byte_object)
        return DataRecord(
            read_policy=d[DATA_RECORD_READ_POLICY],
            write_policy=d[DATA_RECORD_WRITE_POLICY],
            owner_public_key=self.deserialize_public_key(d[DATA_RECORD_OWNER_PUBLIC_KEY]),
            write_public_key=self.deserialize_public_key(d[DATA_RECORD_WRITE_PUBLIC_KEY]),
            encryption_key_read=self.deserialize_abe_ciphertext(
                d[DATA_RECORD_ENCRYPTION_KEY_READ]),
            encryption_key_owner=d[DATA_RECORD_ENCRYPTION_KEY_OWNER],
            write_private_key=(
                self.deserialize_abe_ciphertext(d[DATA_RECORD_WRITE_SECRET_KEY][0]),
                d[DATA_RECORD_WRITE_SECRET_KEY][1]),
            time_period=d[DATA_RECORD_TIME_PERIOD],
            info=d[DATA_RECORD_INFO],
            data=None
        )

    def serialize_authority_public_keys(self, public_keys: AuthorityPublicKeysStore) -> bytes:
        return self.dumps(public_keys)

    def deserialize_authority_public_keys(self, data: bytes) -> AuthorityPublicKeysStore:
        return self.loads(data)

    def serialize_authority_secret_keys(self, secret_keys: AuthoritySecretKeysStore) -> bytes:
        return self.dumps(secret_keys)

    def deserialize_authority_secret_keys(self, data: bytes) -> AuthoritySecretKeysStore:
        return self.loads(data)

    def serialize_authority_update_keys(self, update_keys: Any) -> bytes:
        return self.dumps(update_keys)

    def deserialize_authority_update_keys(self, data: bytes) -> Any:
        return self.loads(data)

    def serialize_keygen_request(self, request) -> bytes:
        return self.dumps(request)

    def deserialize_keygen_request(self, data: bytes):
        return self.loads(data)

    def serialize_user_secret_keys(self, secret_keys: SecretKeyStore) -> bytes:
        return self.dumps(secret_keys)

    def deserialize_user_secret_keys(self, data: bytes) -> SecretKeyStore:
        return self.loads(data)

    def serialize_registration_data(self, registration_data) -> bytes:
        return self.dumps(registration_data)

    def deserialize_registration_data(self, data: bytes):
        return self.loads(data)

    def loads(self, data: bytes) -> Any:
        io = StringIO(data)
        unpickler = ABEUnpickler(io, self)
        return unpickler.load()

    def dumps(self, obj: Any) -> bytes:
        io = StringIO()
        pickler = ABEPickler(io, self)
        pickler.dump(obj)
        io.flush()
        return io.getvalue()


class ABEPickler(Pickler):
    def __init__(self, file, serializer: BaseSerializer) -> None:
        super().__init__(file)
        self.serializer = serializer

    def persistent_id(self, obj):
        if isinstance(obj, charm.core.math.pairing.pc_element):
            return "pairing.Element", self.serializer.group.serialize(obj)
        # pickle as usual
        return None


class ABEUnpickler(Unpickler):
    def __init__(self, file, serializer: BaseSerializer) -> None:
        super().__init__(file)
        self.serializer = serializer

    def persistent_load(self, pid):
        type, id = pid
        if type == "pairing.Element":
            return self.serializer.group.deserialize(id)
        else:
            # Always raises an error if you cannot return the correct object.
            # Otherwise, the unpickler will think None is the object referenced
            # by the persistent ID.
            raise pickle.UnpicklingError("unsupported persistent object")
