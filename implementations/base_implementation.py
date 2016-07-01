from charm.toolbox.pairinggroup import PairingGroup


class BaseImplementation(object):
    """
    The base implementation provider for different ABE implementations. Acts as an abstract factory for
    implementation specific subclasses of various scheme classes.
    """
    def __init__(self, group=None):
        self.group = PairingGroup('SS512') if group is None else group

    def create_central_authority(self):
        """
        Create a new central authority.
        :return: The central authority of this implementation.
        """
        raise NotImplementedError()

    def create_attribute_authority(self, name):
        """
        Create a new attribute authority.
        :param name: The name of the authority.
        :return: An attribute authority of this implementation
        """
        raise NotImplementedError()
