from typing import Any, Dict

from charm.schemes.abenc.abenc_dacmacs_yj14 import DACMACS
from charm.toolbox.pairinggroup import PairingGroup
from implementations.base_implementation import BaseImplementation, AbeEncryption, SecretKeyStore
from records.global_parameters import GlobalParameters
from scheme.attribute_authority import AttributeAuthority
from scheme.central_authority import CentralAuthority


class DACMACS13Implementation(BaseImplementation):
    def create_attribute_authority(self, name: str) -> AttributeAuthority:
        return DACMACS13AttributeAuthority(name)

    def create_central_authority(self) -> CentralAuthority:
        return DACMACS13CentralAuthority(self.group)

    def abe_encrypt(self, global_parameters: GlobalParameters, public_keys: Dict[str, Any], message: bytes, policy: str,
                    time_period: int) -> AbeEncryption:
        dacmacs = DACMACS(self.group)
        dacmacs.encrypt(global_parameters.scheme_parameters, policy)

    def decryption_keys(self, authorities: Dict[str, AttributeAuthority], secret_keys: SecretKeyStore,
                        time_period: int):
        pass

    def abe_decrypt(self, global_parameters: GlobalParameters, secret_keys: SecretKeyStore, gid: str,
                    ciphertext: AbeEncryption) -> bytes:
        pass

    def serialize_abe_ciphertext(self, ciphertext: AbeEncryption) -> Any:
        pass

    def deserialize_abe_ciphertext(self, dictionary: Any) -> AbeEncryption:
        pass


class DACMACS13CentralAuthority(CentralAuthority):
    def __init__(self, group: PairingGroup):
        super().__init__(group)
        self.global_master_key = None

    def setup(self):
        dacmacs = DACMACS(self.global_parameters.group)
        GPP, GMK = dacmacs.setup()
        self.global_parameters.scheme_parameters = GPP
        self.global_master_key = GMK
        return self.global_parameters


class DACMACS13AttributeAuthority(AttributeAuthority):
    def __init__(self, name: str):
        super().__init__(name)
        self.auth_attrs = None

    def setup(self, central_authority, attributes):
        self.global_parameters = central_authority.global_parameters
        self.attributes = attributes
        dacmacs = DACMACS(self.global_parameters.group)
        self.secret_keys, self.public_keys, self.auth_attrs = dacmacs.setupAuthority(
            central_authority.global_parameters.scheme_parameters,
            self.name, self.attributes, {})

    def keygen(self, user, attributes, time_period):
        secret_keys = {}
        for attribute in attributes:
            self.keygen_attribute(user, attribute, time_period, secret_keys)
        return secret_keys

    def keygen_attribute(self, user, attribute, time_period, secret_keys):
        dacmacs = DACMACS(self.global_parameters.group)
        user_secret, user_public = user.registration_data
        return dacmacs.keygen(self.global_parameters.scheme_parameters, (self.secret_keys, self.public_keys, self.auth_attrs), attribute, user_public, secret_keys)



