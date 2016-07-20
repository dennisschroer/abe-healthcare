from charm.toolbox.pairinggroup import PairingGroup
from records.global_parameters import GlobalParameters


class CentralAuthority(object):
    """
    The central authority is only required during the setup phase for determining the global parameters, required
    for the attribute authorities and users to work.
    """

    def __init__(self, group: PairingGroup):
        """
        Creates a new central authority.
        :param group: The (bilinear) group to use.
        """
        self.global_parameters = GlobalParameters(group=group, scheme_parameters=None)

    def setup(self):
        """
        Setup the central authority, creating the global parameters to be used.
        """
        raise NotImplementedError
