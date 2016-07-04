from implementations.base_implementation import BaseImplementation
from charm.schemes.abenc.abenc_maabe_rw15 import MaabeRW15
from scheme.attribute_authority import AttributeAuthority
from scheme.central_authority import CentralAuthority


class RW15(BaseImplementation):
    """
    The implementation according to "Efficient Statically-Secure Large-Universe Multi-Authority Attribute-Based Encryption"

    :paper:     Efficient Statically-Secure Large-Universe Multi-Authority Attribute-Based Encryption
    :authors:   Rouselakis, Yannis and Waters, Brent
    :year:      2015
    """
    def __init__(self, group=None):
        super().__init__(group)

    def create_attribute_authority(self, name):
        central_authority = RWAttributeAuthority(self.group, name)
        return central_authority

    def create_central_authority(self):
        central_authority = RW15CentralAuthority(self.group)
        return central_authority


class RW15CentralAuthority(CentralAuthority):
    def setup(self):
        maabe = MaabeRW15(self.group)
        self.global_parameters.scheme = maabe.setup()


class RWAttributeAuthority(AttributeAuthority):
    def setup(self, central_authority, attributes):
        self.global_parameters = central_authority.global_parameters
        maabe = MaabeRW15(self.global_parameters.group)
        self.public_keys, self.secret_keys = maabe.authsetup(central_authority.global_parameters.scheme, self.name)

    def keygen(self, user, attributes):
        maabe = MaabeRW15(self.global_parameters.group)
        return maabe.multiple_attributes_keygen(self.global_parameters.scheme, self.secret_keys, user.gid, attributes)

