import json
import pickle


class Storage(object):
    def serialize_data_record_meta(self, data_record, implementation):
        """
        Serialize a data record
        :param data_record:
        :type data_record: records.data_record.DataRecord
        :return: A generator which yields the serialized fields
        """
        return pickle.dumps({
            'rp': data_record.read_policy.encode('UTF-8'),
            'wp': data_record.write_policy.encode('UTF-8'),
            'opk': data_record.owner_public_key.exportKey('DER'),
            'wpk': data_record.write_public_key.exportKey('DER'),
            'ekr': implementation.serialize_abe_ciphertext(data_record.encryption_key_read),
            'eko': data_record.encryption_key_owner,
            # 'wsk': implementation.serialize_abe_ciphertext(data_record.write_private_key)
        })
        # yield data_record.read_policy.encode('UTF-8')
        # yield data_record.write_policy.encode('UTF-8')
        # yield data_record.owner_public_key.exportKey('DER')
        # yield data_record.write_public_key.exportKey('DER')
        # yield pickle.dumps(implementation.serialize_abe_ciphertext(data_record.encryption_key_read))
        # yield data_record.encryption_key_owner
        # yield pickle.dumps(implementation.serialize_abe_ciphertext(data_record.write_private_key))
        # yield data_record.data

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
