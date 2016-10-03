from typing import Any

from authority.attribute_authority import AttributeAuthority
from shared.connection.base_connection import BaseConnection
from shared.implementations.serializer.base_serializer import BaseSerializer


class UserAttributeAuthorityConnection(BaseConnection):
    def __init__(self, attribute_authority: AttributeAuthority, serializer: BaseSerializer = None,
                 benchmark: bool = False) -> None:
        super().__init__(benchmark)
        self.attribute_authority = attribute_authority
        self.serializer = serializer

    def request_public_keys(self, time_period: int) -> Any:
        response = self.attribute_authority.public_keys(time_period)
        # if self.benchmark:
        #     self.add_benchmark('out public_keys', (time_period.bit_length() + 7) // 8)
        #     self.add_benchmark('in public_keys', len(self.serializer.serialize_authority_public_keys(response)))
        return response

    def request_keygen(self, gid: str, registration_data: Any, attributes: list, time_period: int):
        request = {
            'gid': gid,
            'registration_data': registration_data,
            'attributes': attributes,
            'time_period': time_period
        }
        response = self.attribute_authority.keygen(gid, registration_data, attributes, time_period)
        if self.benchmark:
            self.add_benchmark('Keygen out', len(self.serializer.serialize_keygen_request(request)))
            self.add_benchmark('Keygen in', len(self.serializer.serialize_user_secret_keys(response)))
        return response

    def request_update_keys(self, time_period):
        response = self.attribute_authority.update_keys(time_period)
        if self.benchmark:
            self.add_benchmark('Update Keys out', (time_period.bit_length() + 7) // 8)
            self.add_benchmark('Update Keys in', len(self.serializer.serialize_authority_update_keys(response)))
        return response
