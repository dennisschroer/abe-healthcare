class CentralAuthority(object):
    def __init__(self, group):
        self.group = group
        self.global_parameters = None

    def setup(self):
        raise NotImplementedError
