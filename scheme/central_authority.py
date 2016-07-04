from records.global_parameters import GlobalParameters


class CentralAuthority(object):
    def __init__(self, group):
        self.global_parameters = GlobalParameters(group=group)

    def setup(self):
        raise NotImplementedError
