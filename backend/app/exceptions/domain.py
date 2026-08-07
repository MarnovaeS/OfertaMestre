class DomainConflictError(Exception):
    def __init__(self, message: str = "Resource already exists") -> None:
        self.message = message
        super().__init__(message)


class DomainNotFoundError(Exception):
    def __init__(self, message: str = "Resource not found") -> None:
        self.message = message
        super().__init__(message)
