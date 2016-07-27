from typing import Any, Dict

from authority.attribute_authority import AttributeAuthority
from charm.schemes.abenc.abenc_maabe_rw15 import PairingGroup
from charm.schemes.abenc.dabe_rd13 import DabeRD13
from charm.toolbox.secretutil import SecretUtil
from exception.policy_not_satisfied_exception import PolicyNotSatisfiedException
from implementations.base_implementation import BaseImplementation, SecretKeyStore, AbeEncryption
from implementations.serializer.base_serializer import BaseSerializer
from model.records.global_parameters import GlobalParameters
from service.central_authority import CentralAuthority
from utils.attribute_util import add_time_period_to_attribute, translate_policy_to_access_structure
from utils.dict_utils import merge_dicts


class RD13Implementation(BaseImplementation):
    """
    The implementation according to
    "Decentralized Ciphertext-Policy Attribute-Based Encryption Scheme with Fast Decryption"

    :paper:     Decentralized Ciphertext-Policy Attribute-Based Encryption Scheme with Fast Decryption
    :authors:   Rao, Y. Sreenivasa and Dutta, Ratna
    :year:      2013
    """

    def __init__(self, group: PairingGroup = None) -> None:
        super().__init__(group)
        self._serializer = None  # type: BaseSerializer

    def create_attribute_authority(self, name: str) -> AttributeAuthority:
        return RD13AttributeAuthority(name)

    def create_central_authority(self) -> CentralAuthority:
        return RD13CentralAuthority(self.group)

    def create_serializer(self) -> BaseSerializer:
        if self._serializer is None:
            self._serializer = RD13Serializer(self.group)
        return self._serializer

    def merge_public_keys(self, authorities: Dict[str, AttributeAuthority], time_period: int) -> Dict[str, Any]:
        return merge_dicts(*[authority.public_keys_for_time_period(time_period) for authority in authorities.values()])

    def abe_encrypt(self, global_parameters: GlobalParameters, public_keys: Dict[str, Any], message: bytes,
                    policy: str, time_period: int) -> AbeEncryption:
        dabe = DabeRD13(self.group)
        util = SecretUtil(self.group, verbose=False)
        parsed_policy = util.createPolicy(policy)
        access_structure = translate_policy_to_access_structure(parsed_policy)
        # Now we add times to the attributes
        access_structure = list(map(
            lambda authorized_set: [
                add_time_period_to_attribute(attribute, time_period)
                for attribute
                in authorized_set],
            access_structure))

        return dabe.encrypt(global_parameters.scheme_parameters, public_keys, message, access_structure)

    def decryption_keys(self, global_parameters: GlobalParameters, authorities: Dict[str, AttributeAuthority],
                        secret_keys: SecretKeyStore,
                        registration_data: Any, ciphertext: AbeEncryption, time_period: int):
        pass

    def abe_decrypt(self, global_parameters: GlobalParameters, secret_keys: SecretKeyStore, gid: str,
                    ciphertext: AbeEncryption, registration_data) -> bytes:
        dabe = DabeRD13(self.group)
        try:
            return dabe.decrypt(global_parameters.scheme_parameters, secret_keys, ciphertext, gid)
        except Exception:
            raise PolicyNotSatisfiedException()


class RD13CentralAuthority(CentralAuthority):
    def setup(self):
        maabe = DabeRD13(self.global_parameters.group)
        self.global_parameters.scheme_parameters = maabe.setup()
        return self.global_parameters

    def register_user(self, gid: str) -> dict:
        return None


class RD13AttributeAuthority(AttributeAuthority):
    def setup(self, central_authority, attributes):
        self.global_parameters = central_authority.global_parameters
        self.attributes = attributes
        dabe = DabeRD13(self.global_parameters.group)
        # Setting up keys here is useless, as a time period is required
        self._public_keys = {}
        self._secret_keys = {}

    def public_keys_for_time_period(self, time_period: int) -> Any:
        if time_period not in self._public_keys:
            self.generate_keys_for_time_period(time_period)
        return self._public_keys[time_period]

    def secret_keys_for_time_period(self, time_period: int) -> Any:
        if time_period not in self._secret_keys:
            self.generate_keys_for_time_period(time_period)
        return self._secret_keys[time_period]

    def generate_keys_for_time_period(self, time_period):
        """
        Generate the public and secret keys for the given time period.
        :param time_period: The time period
        """
        attributes = list(map(lambda x: add_time_period_to_attribute(x, time_period), self.attributes))

        dabe = DabeRD13(self.global_parameters.group)
        pk, sk = dabe.authsetup(self.global_parameters.scheme_parameters, attributes)

        self._public_keys[time_period] = pk
        self._secret_keys[time_period] = sk

    def keygen(self, gid, registration_info, attributes, time_period):
        attributes = list(map(lambda x: add_time_period_to_attribute(x, time_period), self.attributes))
        dabe = DabeRD13(self.global_parameters.group)
        return dabe.keygen(self.global_parameters.scheme_parameters, self.secret_keys_for_time_period(time_period),
                           gid, attributes)


class RD13Serializer(BaseSerializer):
    def serialize_abe_ciphertext(self, ciphertext: AbeEncryption) -> Any:
        result = {
            'A': ciphertext['A']
        }
        for i in range(0, len(ciphertext['A'])):
            result[str(i)] = {
                '1': self.group.serialize(ciphertext[i]['c_1']),
                '2': self.group.serialize(ciphertext[i]['c_2']),
                '3': self.group.serialize(ciphertext[i]['c_3'])
            }
        return result

    def deserialize_abe_ciphertext(self, dictionary: Any) -> AbeEncryption:
        result = {
            'A': dictionary['A']
        }
        for i in range(0, len(dictionary['A'])):
            result[i] = {  # type: ignore
                'c_1': self.group.deserialize(dictionary[str(i)]['1']),
                'c_2': self.group.deserialize(dictionary[str(i)]['2']),
                'c_3': self.group.deserialize(dictionary[str(i)]['3'])
            }
        return result
