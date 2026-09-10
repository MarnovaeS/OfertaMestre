class AwinIntegrationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AwinConfigurationError(AwinIntegrationError):
    pass


class AwinApiError(AwinIntegrationError):
    pass


class AwinUnauthorizedError(AwinApiError):
    pass


class AwinForbiddenError(AwinApiError):
    pass


class AwinRateLimitError(AwinApiError):
    pass


class AwinServerError(AwinApiError):
    pass
