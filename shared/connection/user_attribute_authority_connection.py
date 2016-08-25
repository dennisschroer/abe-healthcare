from typing import Dict, Any

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

    def public_keys_for_time_period(self, time_period: int) -> Any:
        response = self.attribute_authority.public_keys_for_time_period(time_period)
        if self.benchmark:
            self.add_benchmark('< public_keys_for_time_period', len(self.serializer.global_parameters(response)))
        return response
