from scheme.central_authority import CentralAuthority
from scheme.user import User


class AttributeAuthority(object):
    """
    The attribute authority is an authority responsible for a (disjoint) subset of attributes.
    The authority is able to issue secret keys to users for these attributes.
    """
    def __init__(self, name):
        """
        Create a new attribute authority.
        :param name: The name of the authority.
        """
        self.name = name
        self.public_keys = None
        self.secret_keys = None
        self.global_parameters = None

    def setup(self, central_authority: CentralAuthority, attributes: list):
        """
        Setup this attribute authority.
        :param central_authority: The central authority to get the global parameters from.
        :param attributes: The attributes managed by this authority.
        """
        raise NotImplementedError

    def keygen(self, user: User, attributes: list):
        """
        Generate secret keys for a user.
        :param user: The user to generate the keys for.
        :param attributes: The attributes to embed in the secret key.
        :return: The secret keys.

        Note: this method does not check whether the user owns the attribute.
        """
        raise NotImplementedError
