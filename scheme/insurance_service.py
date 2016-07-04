class InsuranceService(object):
    def __init__(self, global_parameters):
        self.global_parameters = global_parameters
        self.authorities = {}

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
