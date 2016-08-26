from typing import Dict, Any

import sys

from authority.attribute_authority import AttributeAuthority
from service.insurance_service import InsuranceService
from shared.connection.base_connection import BaseConnection
from shared.model.global_parameters import GlobalParameters
from shared.model.records.create_record import CreateRecord
from shared.model.records.data_record import DataRecord
from shared.model.records.policy_update_record import PolicyUpdateRecord
from shared.model.records.update_record import UpdateRecord
from shared.serializer.pickle_serializer import PickleSerializer


class UserAttributeAuthorityConnection(BaseConnection):
    def __init__(self, attribute_authority: AttributeAuthority, serializer: PickleSerializer = None,
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
