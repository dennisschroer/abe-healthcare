from scheme.storage import Storage


class InsuranceService(object):
    def __init__(self, global_parameters):
        self.global_parameters = global_parameters
        self.storage = Storage()
        self.authorities = {}
        self.records = {}

    def add_authority(self, attribute_authority):
        """
        Add an attribute authority.
        :param attribute_authority: The attribute authority to add.
         :type attribute_authority: scheme.attribute_authority.AttributeAuthority
        """
        self.authorities[attribute_authority.name] = attribute_authority

    def merge_public_keys(self):
        result = {}
        for name in self.authorities:
            result[name] = self.authorities[name].public_keys
        return result

    def create(self, create_record):
        # In future possibly adapt and check the record
        return self.add(create_record)

    def add(self, record):
        # In future store the record
        name = 'test'

        self.records[name] = record
        generator = self.storage.serialize_data_record(record, self.global_parameters.group)

        f = open('data/name.dat', 'wb')


        print('== SERIALIZED RECORD ==')
        try:
            for line in generator:
                print(line)
                f.write(line)
                f.write("\n".encode('UTF-8'))
        except StopIteration:
            pass
        print('== END SERIALIZED RECORD ==')
        f.close()
        return name

    def get(self, location):
        """
        Get a data record from the given location.
        :param location: The location of the record.
        :return: The record or None.

        >>> service = InsuranceService(None)
        >>> location = service.add({'data': 'TEST'})
        >>> service.get(location) is not None
        True
        >>> service.get(location) == {'data': 'TEST'}
        True
        """
        return self.records[location] if location in self.records else None
