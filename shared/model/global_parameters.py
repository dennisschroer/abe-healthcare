from charm.toolbox.pairinggroup import PairingGroup
from shared.utils.dict_utils import dict_equals_except_functions


class GlobalParameters(object):
    def __init__(self, group: PairingGroup, scheme_parameters: dict = None) -> None:
        self.group = group
        self.scheme_parameters = scheme_parameters

    def __eq__(self, other):
        return isinstance(other, GlobalParameters) \
               and self.group.groupSetting() == other.group.groupSetting() \
               and self.group.groupType() == other.group.groupType() \
               and dict_equals_except_functions(self.scheme_parameters, other.scheme_parameters)
