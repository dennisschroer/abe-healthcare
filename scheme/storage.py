import pickle
import os

from records.data_record import DataRecord

DATA_RECORD_READ_POLICY = 'rp'
DATA_RECORD_WRITE_POLICY = 'wp'
DATA_RECORD_OWNER_PUBLIC_KEY = 'opk'
DATA_RECORD_WRITE_PUBLIC_KEY = 'wpk'
DATA_RECORD_ENCRYPTION_KEY_READ = 'ekr'
DATA_RECORD_ENCRYPTION_KEY_OWNER = 'eko'
DATA_RECORD_WRITE_SECRET_KEY = 'wsk'
DATA_RECORD_INFO = 'i'


class Storage(object):
    def __init__(self):
        if not os.path.exists('data/storage'):
            os.makedirs('data/storage')

    def serialize_data_record_meta(self, data_record, implementation):
        """
        Serialize a data record
        :param data_record:
        :type data_record: records.data_record.DataRecord
        :param implementation: The implementation of the scheme, used for serializing the ciphertext.
        :type implementation: implementations.base_implementation.BaseImplementation
        :return: A generator which yields the serialized fields
        """
        return pickle.dumps({
            DATA_RECORD_READ_POLICY: data_record.read_policy.encode('UTF-8'),
            DATA_RECORD_WRITE_POLICY: data_record.write_policy.encode('UTF-8'),
            DATA_RECORD_OWNER_PUBLIC_KEY: data_record.owner_public_key.exportKey('DER'),
            DATA_RECORD_WRITE_PUBLIC_KEY: data_record.write_public_key.exportKey('DER'),
            DATA_RECORD_ENCRYPTION_KEY_READ: implementation.serialize_abe_ciphertext(data_record.encryption_key_read),
            DATA_RECORD_ENCRYPTION_KEY_OWNER: data_record.encryption_key_owner,
            DATA_RECORD_INFO: data_record.info,
            DATA_RECORD_WRITE_SECRET_KEY: (
            implementation.serialize_abe_ciphertext(data_record.write_private_key[0]), data_record.write_private_key[1])
        })

    def deserialize_data_record_meta(self, byte_object, implementation):
        d = pickle.loads(byte_object)
        return DataRecord(
            read_policy=d[DATA_RECORD_READ_POLICY],
            write_policy=d[DATA_RECORD_WRITE_POLICY],
            owner_public_key=implementation.pke_import_key(d[DATA_RECORD_OWNER_PUBLIC_KEY]),
            write_public_key=implementation.pke_import_key(d[DATA_RECORD_WRITE_PUBLIC_KEY]),
            encryption_key_read=implementation.deserialize_abe_ciphertext(d[DATA_RECORD_ENCRYPTION_KEY_READ]),
            encryption_key_owner=d[DATA_RECORD_ENCRYPTION_KEY_OWNER],
            write_private_key=(implementation.deserialize_abe_ciphertext(d[DATA_RECORD_WRITE_SECRET_KEY][0]),
                               d[DATA_RECORD_WRITE_SECRET_KEY][1]),
            info=d[DATA_RECORD_INFO],
            data=None
        )

    def store(self, name, record, implementation):
        """
        Store the data record.
        :param implementation: The implementation
        :type implementation: implementations.base_implementation.BaseImplementation
        :param name: The location of the data record
        :param record: The record to store
        :type record: records.data_record.DataRecord
        """
        f = open('data/storage/%s.meta' % name, 'wb')
        f.write(self.serialize_data_record_meta(record, implementation))
        f.close()

        f = open('data/storage/%s.dat' % name, 'wb')
        f.write(record.data)
        f.close()

    def load(self, name, implementation):
        f = open('data/storage/%s.meta' % name, 'rb')
        result = self.deserialize_data_record_meta(f.read(), implementation)
        f.close()

        f = open('data/storage/%s.dat' % name, 'rb')
        result.data = f.read()
        f.close()
        return result

    def serialize_abe_encryption(self, ciphertext, group):
        data = self._transform_pairing_elements(ciphertext, group)
        return pickle.dumps(ciphertext)
        # return json.dumps(ciphertext, default=lambda x: self.json_serialize_default(x, group))

    def json_serialize_default(self, o, group):
        return group.serialize(o)

    def _transform_pairing_elements(self, data, group):
        print(type(data))
        print(data.__class__)
        if type(data) is dict:
            for (key, value) in data.items():
                data[key] = self._transform_pairing_elements(value, group)
        elif type(data) is list or type(data) is tuple:
            for i in range(0, len(data)):
                data[i] = self._transform_pairing_elements(data[i], group)
        elif data.__class__.__name__ == 'Element':
            return group.serialize(data)
        else:
            return data
