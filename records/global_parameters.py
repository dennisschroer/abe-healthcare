from charm.toolbox.pairinggroup import PairingGroup


class GlobalParameters(object):
    def __init__(self, group: PairingGroup, scheme_parameters: dict = None) -> None:
        self.group = group
        self.scheme_parameters = scheme_parameters
