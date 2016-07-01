class User(object):
    def __init__(self):
        self.secret_keys = {}

    def issue_secret_keys(self, secret_keys):
        """
        Issue new secret keys to this user.
        :param secret_keys:
        :type secret_keys: dict
        :return:
        """
        self.secret_keys.update(secret_keys)
