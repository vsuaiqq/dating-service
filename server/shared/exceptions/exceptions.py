class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class NotFoundException(AppException):
    def __init__(self, message="Not found", details=None):
        super().__init__(message, 404, details)

class TokenException(AppException):
    def __init__(self, message="Token is missing or invalid", details=None):
        super().__init__(message, 401, details)
