from typing import Dict, Any, List, Union

from charm.schemes.abenc.abenc_maabe_rw15 import PairingGroup
from charm.schemes.abenc.abenc_taac_ylcwr12 import Taac
from charm.toolbox.secretutil import SecretUtil
from exception.policy_not_satisfied_exception import PolicyNotSatisfiedException
from implementations.base_implementation import BaseImplementation, SecretKeyStore, AbeEncryption
from records.global_parameters import GlobalParameters
from scheme.attribute_authority import AttributeAuthority
from scheme.central_authority import CentralAuthority

# The height of the binary trees in the implementation. The number of allowed users is 2^(height-1)
from scheme.user import User
from utils.dict_utils import merge_dicts

BINARY_TREE_HEIGHT = 9


class TAAC12Implementation(BaseImplementation):
    """
    The implementation according to "TAAC: Temporal Attribute-based Access Control for Multi-Authority Cloud Storage Systems"

    :paper:     TAAC: Temporal Attribute-based Access Control for Multi-Authority Cloud Storage Systems
    :authors:   Yang, Kan and Liu, Zhen and Cao, Zhenfu and Jia, Xiaohua and Wong, Duncan S and Ren, Kui
    :year:      2012
    """

    decryption_keys_required = True

    def __init__(self, group: PairingGroup = None) -> None:
        super().__init__(group)

    def create_attribute_authority(self, name: str) -> AttributeAuthority:
        return TAAC12AttributeAuthority(name)

    def create_central_authority(self) -> CentralAuthority:
        return TAAC12CentralAuthority(self.group)

    def abe_encrypt(self, global_parameters: GlobalParameters, public_keys: Dict[str, Any], message: bytes,
                    policy: str, time_period: int) -> AbeEncryption:
        taac = Taac(self.group)
        return taac.encrypt(global_parameters.scheme_parameters, public_keys, message, policy, time_period)

    def decryption_keys(self, authorities: Dict[str, Any], secret_keys: SecretKeyStore, time_period: int):
        update_keys = []
        taac = Taac(self.group)
        for authority_name in authorities:
            update_keys.append(authorities[authority_name].generate_update_keys(time_period))
        merged_update_keys = Taac.merge_timed_keys(*update_keys)
        return taac.decryption_keys_computation(secret_keys, merged_update_keys)

    def abe_decrypt(self, global_parameters: GlobalParameters, decryption_keys: SecretKeyStore, gid: str,
                    ciphertext: AbeEncryption) -> bytes:
        taac = Taac(self.group)
        try:
            return taac.decrypt(global_parameters.scheme_parameters, decryption_keys, ciphertext, gid)
        except Exception:
            raise PolicyNotSatisfiedException()

    def merge_public_keys(self, authorities: Dict[str, AttributeAuthority], time_period) -> Dict[str, Any]:
        """
        Merge the public keys of the attribute authorities to a single entity containing all
        public keys.
        :param authorities: A dict from authority name to authority
        :return: A dict containing the public keys of the authorities.

        >>> from scheme.attribute_authority import AttributeAuthority
        >>> a1 = AttributeAuthority('A1')
        >>> a2 = AttributeAuthority('A2')
        >>> a1.public_keys = {'foo': 'bar'}
        >>> a2.public_keys = {'a': 'b'}
        >>> taac_implementation = TAAC12Implementation()
        >>> public_keys = taac_implementation.merge_public_keys({a1.name: a1, a2.name: a2})
        >>> public_keys == {'foo': 'bar', 'a': 'b'}
        True
        """
        return merge_dicts(*[authority.public_keys_for_time_period(time_period) for name, authority in authorities.items()])

    def deserialize_abe_ciphertext(self, dictionary: Any) -> AbeEncryption:
        util = SecretUtil(self.group, verbose=False)
        # Parse the policy
        policy = util.createPolicy(dictionary['A'])
        attributes = util.getAttributeList(policy)
        result = {
            'A': dictionary['A'],
            't': dictionary['t'],
            'c': self.group.deserialize(dictionary['c'])
        }
        for attribute in attributes:
            result[attribute] = {
                'c_1': self.group.deserialize(dictionary[attribute]['1']),
                'c_2': self.group.deserialize(dictionary[attribute]['2']),
                'c_3': self.group.deserialize(dictionary[attribute]['3']),
                'c_4': self.group.deserialize(dictionary[attribute]['4'])
            }
        return result

    def serialize_abe_ciphertext(self, ciphertext: AbeEncryption) -> Any:
        # ct = {'A': access_policy, 't': t, 'c': c}
        # for attribute in vshares.keys():
        #     r = self.group.random(ZR)
        #     c_1 = (pair(gp['g'], gp['g']) ** vshares[attribute]) * (pk[attribute]['e(g,g)^a'] ** r)
        #     c_2 = (gp['g'] ** ushares[attribute]) * (pk[attribute]['g^b'] ** r)
        #     c_3 = gp['g'] ** r
        #     c_4 = pk['H'](attribute, t) ** r
        #     ct[attribute] = {'c_1': c_1, 'c_2': c_2, 'c_3': c_3, 'c_4': c_4}
        util = SecretUtil(self.group, verbose=False)
        # Parse the policy
        policy = util.createPolicy(ciphertext['A'])
        attributes = util.getAttributeList(policy)

        result = {
            'A': ciphertext['A'],
            't': ciphertext['t'],
            'c': self.group.serialize(ciphertext['c'])
        }
        for attribute in attributes:
            result[attribute] = {
                '1': self.group.serialize(ciphertext[attribute]['c_1']),
                '2': self.group.serialize(ciphertext[attribute]['c_2']),
                '3': self.group.serialize(ciphertext[attribute]['c_3']),
                '4': self.group.serialize(ciphertext[attribute]['c_4'])
            }
        return result


class TAAC12CentralAuthority(CentralAuthority):
    def register_user(self, gid: str) -> dict:
        return None

    def setup(self):
        taac = Taac(self.global_parameters.group)
        self.global_parameters.scheme_parameters = taac.setup()
        return self.global_parameters


class TAAC12AttributeAuthority(AttributeAuthority):
    def __init__(self, name):
        super().__init__(name)
        self.states = None  # type: dict
        self.update_keys = {}  # type: dict

    def setup(self, central_authority, attributes):
        self.global_parameters = central_authority.global_parameters
        self.attributes = attributes
        taac = Taac(self.global_parameters.group)
        self.public_keys, self.secret_keys, self.states = taac.authsetup(
            central_authority.global_parameters.scheme_parameters, attributes, BINARY_TREE_HEIGHT)

    def keygen(self, gid, registration_data, attributes, time_period):
        taac = Taac(self.global_parameters.group)
        return taac.keygen(self.global_parameters.scheme_parameters, self.secret_keys, self.states, gid,
                           attributes)

    def generate_update_keys(self, time_period: int) -> dict:
        if time_period not in self.update_keys:
            taac = Taac(self.global_parameters.group)
            self.update_keys[time_period] = taac.generate_update_keys(self.global_parameters.scheme_parameters, self.public_keys, self.secret_keys, {},
                                      time_period, self.attributes)
        return self.update_keys[time_period]
