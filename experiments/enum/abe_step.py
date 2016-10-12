from enum import Enum


class ABEStep(Enum):
    setup = 1
    authsetup = 2
    register = 3
    keygen = 4
    encrypt = 5
    update_keys = 7
    decrypt = 8
    data_update = 9
    policy_update = 10
