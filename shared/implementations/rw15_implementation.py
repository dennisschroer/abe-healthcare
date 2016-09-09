from typing import Any, Dict

from authority.attribute_authority import AttributeAuthority
from charm.schemes.abenc.abenc_maabe_rw15 import MaabeRW15
from charm.toolbox.secretutil import SecretUtil
from charm.toolbox.pairinggroup import G2, PairingGroup
from service.central_authority import CentralAuthority
from shared.exception.policy_not_satisfied_exception import PolicyNotSatisfiedException
from shared.implementations.base_implementation import BaseImplementation, SecretKeyStore, AbeEncryption
from shared.implementations.serializer.base_serializer import BaseSerializer
from shared.model.global_parameters import GlobalParameters
from shared.utils.attribute_util import add_time_period_to_attribute, add_time_periods_to_policy


class RW15Implementation(BaseImplementation):
    """
    The implementation according to
    "Efficient Statically-Secure Large-Universe Multi-Authority Attribute-Based Encryption"

    :paper:     Efficient Statically-Secure Large-Universe Multi-Authority Attribute-Based Encryption
    :authors:   Rouselakis, Yannis and Waters, Brent
    :year:      2015
    """

    def __init__(self, group: PairingGroup = None) -> None:
        super().__init__(group)
        self._serializer = None  # type: BaseSerializer

    def get_name(self):
        return "RW-ABE"

    def create_attribute_authority(self, name: str, storage_path: str = None) -> AttributeAuthority:
        return RW15AttributeAuthority(name, self.serializer, storage_path=storage_path)

    def create_central_authority(self, storage_path: str = None) -> CentralAuthority:
        return RW15CentralAuthority(self.group, self.serializer, storage_path=storage_path)

    @property
    def serializer(self) -> BaseSerializer:
        if self._serializer is None:
            self._serializer = RW15Serializer(self.group, self.public_key_scheme)
        return self._serializer

    def abe_encrypt(self, global_parameters: GlobalParameters, public_keys: Dict[str, Any], message: bytes,
                    policy: str, time_period: int) -> AbeEncryption:
        maabe = MaabeRW15(self.group)
        policy = add_time_periods_to_policy(policy, time_period, self.group)
        return maabe.encrypt(global_parameters.scheme_parameters, public_keys, message, policy)

    def abe_decrypt(self, global_parameters: GlobalParameters, secret_keys: SecretKeyStore, gid: str,
                    ciphertext: AbeEncryption, registration_data) -> bytes:
        maabe = MaabeRW15(self.group)

        util = SecretUtil(self.group)
        policy = util.createPolicy(ciphertext['policy'])
        coefficients = util.getCoefficients(policy)
        pruned_list = util.prune(policy, secret_keys.keys())

        try:
            return maabe.decrypt(global_parameters.scheme_parameters, {'GID': gid, 'keys': secret_keys}, ciphertext)
        except Exception:
            raise PolicyNotSatisfiedException()


class RW15CentralAuthority(CentralAuthority):
    def register_user(self, gid: str) -> dict:
        return None

    def central_setup(self):
        maabe = MaabeRW15(self.global_parameters.group)
        self.global_parameters.scheme_parameters = maabe.setup()
        return self.global_parameters


class RW15AttributeAuthority(AttributeAuthority):
    def setup(self, central_authority, attributes):
        self.global_parameters = central_authority.global_parameters
        self.attributes = attributes
        maabe = MaabeRW15(self.global_parameters.group)
        self._public_keys, self._secret_keys = maabe.authsetup(central_authority.global_parameters.scheme_parameters,
                                                               self.name)

    def _keygen(self, gid, registration_data, attributes, time_period):
        maabe = MaabeRW15(self.global_parameters.group)
        attributes = map(lambda x: add_time_period_to_attribute(x, time_period), attributes)
        return maabe.multiple_attributes_keygen(self.global_parameters.scheme_parameters,
                                                self.secret_keys(time_period), gid,
                                                attributes)


class RW15Serializer(BaseSerializer):
    def serialize_global_scheme_parameters(self, scheme_parameters):
        # gp = {'g1': g1, 'g2': g2, 'egg': egg, 'H': H, 'F': F}
        return {
            'g1': self.group.serialize(scheme_parameters['g1']),
            'g2': self.group.serialize(scheme_parameters['g2']),
            'egg': self.group.serialize(scheme_parameters['egg'])
        }

    def deserialize_global_scheme_parameters(self, data):
        # gp = {'g1': g1, 'g2': g2, 'egg': egg, 'H': H, 'F': F}
        return {
            'g1': self.group.deserialize(data['g1']),
            'g2': self.group.deserialize(data['g2']),
            'egg': self.group.deserialize(data['egg']),
            'H': lambda x: self.group.hash(x, G2),
            'F': lambda x: self.group.hash(x, G2)
        }

    def serialize_abe_ciphertext(self, ciphertext: AbeEncryption) -> Any:
        # {'policy': policy_str, 'C0': C0, 'C1': C1, 'C2': C2, 'C3': C3, 'C4': C4}
        # C0 = message * (gp['egg'] ** s)
        # C1[i] = gp['egg'] ** secret_shares[i] * pks[auth]['egga'] ** tx
        # C2[i] = gp['g1'] ** (-tx)
        # C3[i] = pks[auth]['gy'] ** tx * gp['g1'] ** zero_shares[i]
        # C4[i] = gp['F'](attr) ** tx
        dictionary = dict()  # type: dict
        return {
            'p': ciphertext['policy'],
            '0': self.group.serialize(ciphertext['C0']),
            '1': {self.replace_attributes(dictionary, k): self.group.serialize(v) for k, v in
                  ciphertext['C1'].items()},
            '2': {self.replace_attributes(dictionary, k): self.group.serialize(v) for k, v in
                  ciphertext['C2'].items()},
            '3': {self.replace_attributes(dictionary, k): self.group.serialize(v) for k, v in
                  ciphertext['C3'].items()},
            '4': {self.replace_attributes(dictionary, k): self.group.serialize(v) for k, v in
                  ciphertext['C4'].items()},
            'd': dictionary
        }

    def deserialize_abe_ciphertext(self, dictionary: Any) -> AbeEncryption:
        return {
            'policy': dictionary['p'],
            'C0': self.group.deserialize(dictionary['0']),
            'C1': {self.undo_attribute_replacement(dictionary['d'], k): self.group.deserialize(v) for k, v in
                   dictionary['1'].items()},
            'C2': {self.undo_attribute_replacement(dictionary['d'], k): self.group.deserialize(v) for k, v in
                   dictionary['2'].items()},
            'C3': {self.undo_attribute_replacement(dictionary['d'], k): self.group.deserialize(v) for k, v in
                   dictionary['3'].items()},
            'C4': {self.undo_attribute_replacement(dictionary['d'], k): self.group.deserialize(v) for k, v in
                   dictionary['4'].items()},
        }
