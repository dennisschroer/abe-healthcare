import json

class Storage(object):
    def serialize_data_record(self, data_record, group):
        """
        Serialize a data record
        :param data_record:
        :type data_record: records.data_record.DataRecord
        :return: A generator which yields the serialized fields
        """
        yield data_record.read_policy.encode('UTF-8')
        yield data_record.write_policy.encode('UTF-8')
        yield data_record.owner_public_key.exportKey('DER')
        yield data_record.write_public_key.exportKey('DER')
        yield self.serialize_abe_encryption(data_record.encryption_key_read, group)
        #yield pickle.dumps(data_record.encryption_key_read)
        yield data_record.encryption_key_owner
        #yield group.serialize(data_record.write_private_key)
        yield data_record.data

    def serialize_abe_encryption(self, ciphertext, group):
        return json.dumps(ciphertext, default=lambda x: self.json_serialize_default(x, group))

    def json_serialize_default(self, o, group):
        return group.serialize(o)