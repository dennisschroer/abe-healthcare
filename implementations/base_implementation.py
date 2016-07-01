from charm.toolbox.pairinggroup import PairingGroup


class BaseImplementation(object):
    def __init__(self, group=None):
        self.group = PairingGroup('SS512') if group is None else group

    def create_central_authority(self):
        raise NotImplementedError()

    def create_attribute_authority(self, name):
        raise NotImplementedError()
