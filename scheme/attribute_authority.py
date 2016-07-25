from typing import Any

from records.global_parameters import GlobalParameters
from scheme.central_authority import CentralAuthority
from scheme.user import User


class AttributeAuthority(object):
    """
    The attribute authority is an authority responsible for a (disjoint) subset of attributes.
    The authority is able to issue secret keys to users for these attributes.
    """

    def __init__(self, name: str) -> None:
        """
        Create a new attribute authority.
        :param name: The name of the authority.
        """
        self.name = name
        self.attributes = []  # type: list
        self.public_keys = None  # type: Any
        self.secret_keys = None  # type: Any
        self.global_parameters = None  # type: GlobalParameters

    def setup(self, central_authority: CentralAuthority, attributes: list):
        """
        Setup this attribute authority.
        :param central_authority: The central authority to get the global parameters from.
        :param attributes: The attributes managed by this authority.
        """
        raise NotImplementedError

    def keygen(self, user: User, attributes: list, time_period: int):
        """
        Generate secret keys for a user.
        :param user: The user
        :param attributes: The attributes to embed in the secret key.
        :param time_period: The time period for which to generate the keys. In some
        schemes, this value is not used.
        :return: The secret keys.

        Note: this method does not check whether the user owns the attribute.
        """
        raise NotImplementedError
