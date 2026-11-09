class AppException(Exception):
    def __init__(self, message: str):
        self.message = message


class NotFoundError(AppException):
    pass


class ConflictError(AppException):
    pass


class ForbiddenError(AppException):
    pass


class TooManyRequestsError(AppException):
    def __init__(self, message: str = "Too many requests. Please try again later.", retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after
