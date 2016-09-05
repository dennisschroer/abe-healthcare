from types import FunctionType
from typing import Dict, Any

from charm.toolbox.pairinggroup import PairingGroup


class GlobalParameters(object):
    def __init__(self, group: PairingGroup, scheme_parameters: dict = None) -> None:
        self.group = group
        self.scheme_parameters = scheme_parameters

    def __eq__(self, other):
        return isinstance(other, GlobalParameters) \
               and self.group.groupSetting() == other.group.groupSetting() \
               and self.group.groupType() == other.group.groupType() \
               and self.scheme_parameters_equal(self.scheme_parameters, other.scheme_parameters)

    @staticmethod
    def scheme_parameters_equal(a: Dict[str, Any], b: Dict[str, Any]):
        if a.keys() != b.keys():
            return False
        for key in a.keys():
            if not isinstance(a[key], FunctionType) or not isinstance(b[key], FunctionType):
                if a[key] != b[key]:
                    return False
        return True
