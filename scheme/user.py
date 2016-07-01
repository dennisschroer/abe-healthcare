class User(object):
    def __init__(self):
        self.secret_keys = {}

    def issue_secret_keys(self, secret_keys):
        """
        Issue new secret keys to this user.
        :param secret_keys:
        :type secret_keys: dict

        >>> user = User()
        >>> user.secret_keys
        {}
        >>> user.issue_secret_keys({'a': {'foo': 'bar'}})
        >>> user.secret_keys == {'a': {'foo': 'bar'}}
        True
        >>> user.issue_secret_keys({'b': {'bla': 'bla'}})
        >>> user.secret_keys == {'a': {'foo': 'bar'}, 'b': {'bla': 'bla'}}
        True
        """
        self.secret_keys.update(secret_keys)
