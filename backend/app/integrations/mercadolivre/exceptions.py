class MercadoLivreError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class MercadoLivreConfigurationError(MercadoLivreError):
    pass


class MercadoLivreOAuthError(MercadoLivreError):
    pass


class MercadoLivreApiError(MercadoLivreError):
    pass


class MercadoLivreNormalizationError(MercadoLivreError):
    pass


class MercadoLivreUnauthorizedError(MercadoLivreApiError):
    pass


class MercadoLivreForbiddenError(MercadoLivreApiError):
    def __init__(self, message: str, operation: str | None = None) -> None:
        self.operation = operation
        super().__init__(message)


class MercadoLivreNotFoundError(MercadoLivreApiError):
    pass


class MercadoLivreRateLimitError(MercadoLivreApiError):
    pass


class MercadoLivreServerError(MercadoLivreApiError):
    pass


class MercadoLivreAuthorizationRevokedError(MercadoLivreOAuthError):
    pass
