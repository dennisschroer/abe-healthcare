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
        return RWAttributeAuthority(name)

    def create_central_authority(self):
        return RW15CentralAuthority(self.group)

    def create_abe_encryption(self):
        maabe = MaabeRW15(self.group)
        return maabe.encrypt

    def create_abe_decryption(self):
        maabe = MaabeRW15(self.group)
        return maabe.decrypt


class RW15CentralAuthority(CentralAuthority):
    def setup(self):
        maabe = MaabeRW15(self.global_parameters.group)
        self.global_parameters.scheme_parameters = maabe.setup()


class RWAttributeAuthority(AttributeAuthority):
    def setup(self, central_authority, attributes):
        self.global_parameters = central_authority.global_parameters
        maabe = MaabeRW15(self.global_parameters.group)
        self.public_keys, self.secret_keys = maabe.authsetup(central_authority.global_parameters.scheme_parameters,
                                                             self.name)

    def keygen(self, user, attributes):
        maabe = MaabeRW15(self.global_parameters.group)
        return maabe.multiple_attributes_keygen(self.global_parameters.scheme_parameters, self.secret_keys, user.gid,
                                                attributes)
