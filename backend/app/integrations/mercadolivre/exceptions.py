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


class MercadoLivreUnauthorizedError(MercadoLivreApiError):
    pass


class MercadoLivreForbiddenError(MercadoLivreApiError):
    pass


class MercadoLivreNotFoundError(MercadoLivreApiError):
    pass


class MercadoLivreRateLimitError(MercadoLivreApiError):
    pass


class MercadoLivreServerError(MercadoLivreApiError):
    pass


class MercadoLivreAuthorizationRevokedError(MercadoLivreOAuthError):
    pass
