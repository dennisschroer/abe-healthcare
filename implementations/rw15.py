from implementations.base_implementation import BaseImplementation
from charm.schemes.abenc.abenc_maabe_rw15 import MaabeRW15
from scheme.attribute_authority import AttributeAuthority
from scheme.central_authority import CentralAuthority


class RW15(BaseImplementation):
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
        self.global_parameters = maabe.setup()


class RWAttributeAuthority(AttributeAuthority):
    def setup(self, central_authority, attributes):
        maabe = MaabeRW15(central_authority.group)
        self.global_parameters = central_authority.global_parameters
        self.public_keys, self.secret_keys = maabe.authsetup(central_authority.global_parameters, self.name)

    def keygen(self, user, attributes):
        maabe = MaabeRW15(self.global_parameters.group)

