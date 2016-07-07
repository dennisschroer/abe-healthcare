from implementations.base_implementation import BaseImplementation
from charm.schemes.abenc.abenc_maabe_rw15 import MaabeRW15
from scheme.attribute_authority import AttributeAuthority
from scheme.central_authority import CentralAuthority
import base64


class RW15(BaseImplementation):
    """
    The implementation according to "Efficient Statically-Secure Large-Universe Multi-Authority Attribute-Based Encryption"

    :paper:     Efficient Statically-Secure Large-Universe Multi-Authority Attribute-Based Encryption
    :authors:   Rouselakis, Yannis and Waters, Brent
    :year:      2015
    """

    def __init__(self, group=None):
        super().__init__(group)

    def setup_secret_keys(self, user):
        return {'GID': user.gid, 'keys': {}}

    def update_secret_keys(self, secret_keys_base, secret_keys):
        secret_keys_base['keys'].update(secret_keys)

    def create_attribute_authority(self, name):
        return RWAttributeAuthority(name)

    def create_central_authority(self):
        return RW15CentralAuthority(self.group)

    def abe_encrypt(self, global_parameters, public_keys, message, access_policy):
        maabe = MaabeRW15(self.group)
        return maabe.encrypt(global_parameters.scheme_parameters, public_keys, message, access_policy)

    def abe_decrypt(self, global_parameters, secret_keys, ciphertext):
        maabe = MaabeRW15(self.group)
        return maabe.decrypt(global_parameters.scheme_parameters, secret_keys, ciphertext)

    def serialize_abe_ciphertext(self, cp):
        # {'policy': policy_str, 'C0': C0, 'C1': C1, 'C2': C2, 'C3': C3, 'C4': C4}
        # C0 = message * (gp['egg'] ** s)
        # C1[i] = gp['egg'] ** secret_shares[i] * pks[auth]['egga'] ** tx
        # C2[i] = gp['g1'] ** (-tx)
        # C3[i] = pks[auth]['gy'] ** tx * gp['g1'] ** zero_shares[i]
        # C4[i] = gp['F'](attr) ** tx
        dictionary = dict()
        return {
            'p': cp['policy'],
            '0': self.group.serialize(cp['C0']),
            '1': {self.attribute_replacement(dictionary, k): self.group.serialize(v) for k, v in
                  cp['C1'].items()},
            '2': {self.attribute_replacement(dictionary, k): self.group.serialize(v) for k, v in
                  cp['C2'].items()},
            '3': {self.attribute_replacement(dictionary, k): self.group.serialize(v) for k, v in
                  cp['C3'].items()},
            '4': {self.attribute_replacement(dictionary, k): self.group.serialize(v) for k, v in
                  cp['C4'].items()},
            'd': dictionary
        }

    def deserialize_abe_ciphertext(self, d):
        """
        >>> from charm.toolbox.pairinggroup import PairingGroup
        >>> group = PairingGroup('SS512')
        >>> i = RW15(group)
        >>>
        """
        return {
            'policy': d['p'],
            'C0': self.group.deserialize(d['0']),
            'C1': {self.undo_attribute_replacement(d['d'], k): self.group.deserialize(v) for k, v in
                   d['1'].items()},
            'C2': {self.undo_attribute_replacement(d['d'], k): self.group.deserialize(v) for k, v in
                   d['2'].items()},
            'C3': {self.undo_attribute_replacement(d['d'], k): self.group.deserialize(v) for k, v in
                   d['3'].items()},
            'C4': {self.undo_attribute_replacement(d['d'], k): self.group.deserialize(v) for k, v in
                   d['4'].items()},
        }


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
