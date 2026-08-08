class MercadoLivreError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class MercadoLivreConfigurationError(MercadoLivreError):
    pass


class MercadoLivreOAuthError(MercadoLivreError):
    pass


class MercadoLivreAccessDeniedError(MercadoLivreOAuthError):
    pass


class MercadoLivreInvalidStateError(MercadoLivreOAuthError):
    pass


class MercadoLivreExpiredStateError(MercadoLivreOAuthError):
    pass


class MercadoLivreReusedStateError(MercadoLivreOAuthError):
    pass


class MercadoLivreAuthorizationCodeError(MercadoLivreOAuthError):
    pass


class MercadoLivreAuthorizationRevokedError(MercadoLivreOAuthError):
    pass
