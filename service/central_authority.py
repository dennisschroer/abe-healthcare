import os

from charm.toolbox.pairinggroup import PairingGroup
from shared.implementations.serializer.base_serializer import BaseSerializer
from shared.model.global_parameters import GlobalParameters

DEFAULT_STORAGE_PATH = 'data/central_authority'
GLOBAL_PARAMETERS_FILENAME = 'gp.dat'


class CentralAuthority(object):
    """
    The central authority is only required during the setup phase for determining the global parameters, required
    for the attribute authorities and users to work.
    """

    def __init__(self, group: PairingGroup, serializer: BaseSerializer, storage_path: str = None) -> None:
        """
        Creates a new central authority.
        :param group: The (bilinear) group to use.
        """
        self.storage_path = DEFAULT_STORAGE_PATH if storage_path is None else storage_path
        self.global_parameters = GlobalParameters(group=group, scheme_parameters=None)
        self.serializer = serializer
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)

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
        raise NotImplementedError()

    def save_global_parameters(self):
        save_file_path = os.path.join(self.storage_path, GLOBAL_PARAMETERS_FILENAME)
        with open(save_file_path, 'wb') as f:
            f.write(self.serializer.serialize_global_parameters(self.global_parameters))

    def load_global_parameters(self):
        save_file_path = os.path.join(self.storage_path, GLOBAL_PARAMETERS_FILENAME)
        with open(save_file_path, 'rb') as f:
            self.global_parameters = self.serializer.deserialize_global_parameters(f.read())
