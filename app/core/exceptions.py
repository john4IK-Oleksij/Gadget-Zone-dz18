class AppException(Exception):
    def __init__(self, message: str):
        self.message = message


class NotFoundError(AppException):
    pass

class ConflictError(AppException):
    pass