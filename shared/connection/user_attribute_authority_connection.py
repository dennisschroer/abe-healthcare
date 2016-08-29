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

    def public_keys(self, time_period: int) -> Any:
        response = self.attribute_authority.public_keys(time_period)
        if self.benchmark:
            self.add_benchmark('> public_keys', (time_period.bit_length() + 7) // 8)
            self.add_benchmark('< public_keys', len(self.serializer.public_keys(response)))
        return response

    def keygen(self, gid: str, registration_data: Any, attributes: list, time_period: int):
        request = {
            'gid': gid,
            'registration_data': registration_data,
            'attributes': attributes,
            'time_period': time_period
        }
        response = self.attribute_authority.keygen(gid, registration_data, attributes, time_period)
        if self.benchmark:
            self.add_benchmark('> keygen', len(self.serializer.keygen(request)))
            self.add_benchmark('< keygen', len(self.serializer.secret_keys(response)))
        return response
