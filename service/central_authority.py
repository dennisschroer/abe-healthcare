from charm.toolbox.pairinggroup import PairingGroup
from shared.model.global_parameters import GlobalParameters


class CentralAuthority(object):
    """
    The central authority is only required during the setup phase for determining the global parameters, required
    for the attribute authorities and users to work.
    """

    def __init__(self, group: PairingGroup) -> None:
        """
        Creates a new central authority.
        :param group: The (bilinear) group to use.
        """
        self.global_parameters = GlobalParameters(group=group, scheme_parameters=None)

    def central_setup(self):
        """
        Setup the central authority, creating the global parameters to be used.
        """
        raise NotImplementedError

    def register_user(self, gid: str) -> dict:
        """
        Register a new user. Some schemes do nothing with this.
        :param gid: The global identifier of the user to register
        :return: Additional data to store on the user
        """
        raise NotImplementedError
