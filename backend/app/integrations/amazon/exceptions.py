class AmazonIntegrationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AmazonConfigurationError(AmazonIntegrationError):
    pass


class AmazonApiError(AmazonIntegrationError):
    pass


class AmazonUnauthorizedError(AmazonApiError):
    pass


class AmazonForbiddenError(AmazonApiError):
    pass


class AmazonRateLimitError(AmazonApiError):
    pass


class AmazonServerError(AmazonApiError):
    pass
