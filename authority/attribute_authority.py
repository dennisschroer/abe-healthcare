from typing import Any, List, Dict

from service.central_authority import CentralAuthority
from shared.model.global_parameters import GlobalParameters


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
        self.revocation_list = dict()  # type: Dict[int, Dict[str, List[str]]]

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

    def revoke_attribute_indirect(self, gid: str, attribute: str, time_period: int) -> None:
        """
        Indirectly revoke an attribute for a user for a time period by adding it to the revocation list.
        The attribute authority will no longer issue secret keys for this user in the given time period.
        :param gid: The global identifier of the user
        :param attribute: The attribute to revoke
        :param time_period: The time period to revoke for.
        """
        if time_period not in self.revocation_list:
            self.revocation_list[time_period] = dict()
        if attribute not in self.revocation_list[time_period]:
            self.revocation_list[time_period][attribute] = list()
        self.revocation_list[time_period][attribute].append(gid)

    def revocation_list_for_time_period(self, time_period: int) -> Dict[str, List[str]]:
        """
        Gets the revocation list for this authority for a certain time period
        :param time_period: The time period to get the revocation list for.
        :return: A dictionary of attribute name to list of user identifiers.
        """
        return self.revocation_list[time_period] if time_period in self.revocation_list else {}

    def is_revoked(self, gid: str, attribute: str, time_period: int) -> bool:
        """
        Check whether the given attribute is revoked for a user in a time period
        :param gid: The global identifier of the user
        :param attribute: The attribute to check
        :param time_period: The time period to check.
        :return: Whether the attribute is revoked.
        """
        if time_period in self.revocation_list and attribute in self.revocation_list[time_period]:
            return gid in self.revocation_list[time_period][attribute]
        else:
            return False

    def remove_revoked_attributes(self, gid: str, attributes: List[str], time_period: int) -> List[str]:
        return [attribute for attribute in attributes if not self.is_revoked(gid, attribute, time_period)]

    def keygen_valid_attributes(self, gid: str, registration_data: Any, attributes: list, time_period: int):
        valid_attributes = self.remove_revoked_attributes(gid, attributes, time_period)
        return self.keygen(gid, registration_data, valid_attributes, time_period)

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
