class UrlVerifyFail(Exception):
    def __init__(self, message):
        super().__init__(message)


class FailToCreate(Exception):
    def __init__(self):
        super().__init__()
