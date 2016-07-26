class UpdateRecord(object):
    def __init__(self, data: bytes = None, signature: bytes = None) -> None:
        self.data = data
        self.signature = signature
