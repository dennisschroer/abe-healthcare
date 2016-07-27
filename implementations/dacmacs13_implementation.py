from typing import Any, Dict

from authority.attribute_authority import AttributeAuthority
from charm.schemes.abenc.abenc_dacmacs_yj14 import DACMACS
from charm.schemes.abenc.abenc_maabe_rw15 import MaabeRW15, PairingGroup
from charm.toolbox.secretutil import SecretUtil
from exception.policy_not_satisfied_exception import PolicyNotSatisfiedException
from implementations.base_implementation import BaseImplementation, SecretKeyStore, AbeEncryption
from implementations.serializer.base_serializer import BaseSerializer
from model.records.global_parameters import GlobalParameters
from service.central_authority import CentralAuthority
from utils.attribute_util import add_time_period_to_attribute, add_time_periods_to_policy


class DACMACS13Implementation(BaseImplementation):
    """
    The implementation according to
    "DAC-MACS: Effective Data Access Control for Multi-Authority Cloud Storage Systems "

    :paper:     DAC-MACS: Effective Data Access Control for Multi-Authority Cloud Storage Systems
    :authors:   Kan Yang, Xiaohua Jia
    :year:      2013
    """

    decryption_keys_required = True

    def __init__(self, group: PairingGroup = None) -> None:
        super().__init__(group)
        self._serializer = None  # type: BaseSerializer

    def create_attribute_authority(self, name: str) -> AttributeAuthority:
        return DACMACS13AttributeAuthority(name)

    def create_central_authority(self) -> CentralAuthority:
        return DACMACS13CentralAuthority(self.group)

    def create_serializer(self) -> BaseSerializer:
        if self._serializer is None:
            self._serializer = DACMACS13Serializer(self.group)
        return self._serializer

    def abe_encrypt(self, global_parameters: GlobalParameters, public_keys: Dict[str, Any], message: bytes,
                    policy: str, time_period: int) -> AbeEncryption:
        dacmacs = DACMACS(self.group)
        policy = add_time_periods_to_policy(policy, time_period, self.group)
        return dacmacs.encrypt(global_parameters.scheme_parameters, public_keys, message, policy)

    def decryption_keys(self, global_parameters: GlobalParameters, authorities: Dict[str, AttributeAuthority],
                        secret_keys: SecretKeyStore,
                        registration_data: Any, ciphertext: AbeEncryption, time_period: int):
        dacmacs = DACMACS(self.group)
        return dacmacs.generate_token(global_parameters.scheme_parameters, ciphertext, registration_data['public'],
                                      secret_keys)

    def abe_decrypt(self, global_parameters: GlobalParameters, secret_keys: SecretKeyStore, gid: str,
                    ciphertext: AbeEncryption, registration_data) -> bytes:
        dacmacs = DACMACS(self.group)

        try:
            return dacmacs.decrypt(ciphertext, secret_keys, registration_data['secret'])
        except Exception:
            raise PolicyNotSatisfiedException()


class DACMACS13CentralAuthority(CentralAuthority):
    def __init__(self, group=None):
        super().__init__(group)
        self.master_key = None

    def register_user(self, gid: str) -> dict:
        dacmacs = DACMACS(self.global_parameters.group)
        public, private = dacmacs.register_user(self.global_parameters.scheme_parameters)
        cert = private['cert']
        del private['cert']
        return {'public': public, 'private': private, 'cert': cert}

    def setup(self):
        dacmacs = DACMACS(self.global_parameters.group)
        public_key, master_key = dacmacs.setup()
        self.master_key = master_key
        self.global_parameters.scheme_parameters = public_key
        return self.global_parameters


class DACMACS13AttributeAuthority(AttributeAuthority):
    def setup(self, central_authority, attributes):
        self.global_parameters = central_authority.global_parameters
        self.attributes = attributes
        dacmacs = DACMACS(self.global_parameters.group)
        self._public_keys, self._secret_keys = dacmacs.authsetup(
            central_authority.global_parameters.scheme_parameters,
            self.attributes)

    def keygen(self, gid, registration_data, attributes, time_period):
        dacmacs = DACMACS(self.global_parameters.group)
        attributes = map(lambda x: add_time_period_to_attribute(x, time_period), attributes)
        return dacmacs.keygen(self.global_parameters.scheme_parameters,
                              self.secret_keys_for_time_period(time_period),
                              self.public_keys_for_time_period(time_period), attributes, registration_data['cert'])


class DACMACS13Serializer(BaseSerializer):
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
            '1': {self.attribute_replacement(dictionary, k): self.group.serialize(v) for k, v in
                  ciphertext['C1'].items()},
            '2': {self.attribute_replacement(dictionary, k): self.group.serialize(v) for k, v in
                  ciphertext['C2'].items()},
            '3': {self.attribute_replacement(dictionary, k): self.group.serialize(v) for k, v in
                  ciphertext['C3'].items()},
            '4': {self.attribute_replacement(dictionary, k): self.group.serialize(v) for k, v in
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
