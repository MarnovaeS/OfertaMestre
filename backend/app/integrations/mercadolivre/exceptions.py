class MercadoLivreError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class MercadoLivreConfigurationError(MercadoLivreError):
    pass


class MercadoLivreOAuthError(MercadoLivreError):
    pass


class MercadoLivreAuthorizationRevokedError(MercadoLivreOAuthError):
    pass
