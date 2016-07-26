from typing import Any

from model.records.global_parameters import GlobalParameters
from service.central_authority import CentralAuthority


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
        self._public_keys = None  # type: Any
        self._secret_keys = None  # type: Any
        self.global_parameters = None  # type: GlobalParameters

    def setup(self, central_authority: CentralAuthority, attributes: list):
        """
        Setup this attribute authority.
        :param central_authority: The central authority to get the global parameters from.
        :param attributes: The attributes managed by this authority.
        """
        raise NotImplementedError

    def public_keys_for_time_period(self, time_period: int) -> Any:
        """
        Gets the public keys to be used in the given time period.
        :param time_period: The time period
        :return: The public keys for the given time period.
        """
        return self._public_keys

    def secret_keys_for_time_period(self, time_period: int) -> Any:
        """
        Gets the secret/master keys to be used in the given time period.
        :param time_period: The time period
        :return: The secret keys for the given time period.
        """
        return self._secret_keys

    def keygen(self, gid: str, registration_data: Any, attributes: list, time_period: int):
        """
        Generate secret keys for a user.

        :param gid: The global identifier of the user.
        :param registration_data: The registration data of the user.
        :param attributes: The attributes to embed in the secret key.
        :param time_period: The time period for which to generate the keys. In some
        schemes, this value is not used.
        :return: The secret keys.

        Note: this method does not check whether the user owns the attribute.
        """
        raise NotImplementedError
