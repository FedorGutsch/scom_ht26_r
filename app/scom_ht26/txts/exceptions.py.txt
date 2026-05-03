class AppException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code

class NotFoundException(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=404)