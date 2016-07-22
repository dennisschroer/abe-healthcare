from typing import Any, Dict

from implementations.base_implementation import BaseImplementation, AbeEncryption, SecretKeyStore
from records.global_parameters import GlobalParameters
from scheme.attribute_authority import AttributeAuthority
from scheme.central_authority import CentralAuthority


class DACMACS13Implementation(BaseImplementation):
    def deserialize_abe_ciphertext(self, dictionary: Any) -> AbeEncryption:
        pass

    def abe_encrypt(self, global_parameters: GlobalParameters, public_keys: Dict[str, Any], message: bytes, policy: str,
                    time_period: int) -> AbeEncryption:
        pass

    def serialize_abe_ciphertext(self, ciphertext: AbeEncryption) -> Any:
        pass

    def abe_decrypt(self, global_parameters: GlobalParameters, secret_keys: SecretKeyStore, gid: str,
                    ciphertext: AbeEncryption) -> bytes:
        pass

    def create_central_authority(self) -> CentralAuthority:
        pass

    def decryption_keys(self, authorities: Dict[str, AttributeAuthority], secret_keys: SecretKeyStore,
                        time_period: int):
        pass

    def create_attribute_authority(self, name: str) -> AttributeAuthority:
        pass
