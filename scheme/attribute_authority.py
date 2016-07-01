class AttributeAuthority(object):
    def __init__(self, name):
        self.name = name
        self.public_keys = None
        self.secret_keys = None

    def setup(self, central_authority, attributes):
        raise NotImplementedError
