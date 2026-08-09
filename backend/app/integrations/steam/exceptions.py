class SteamIntegrationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class SteamConfigurationError(SteamIntegrationError):
    pass


class SteamApiError(SteamIntegrationError):
    pass


class SteamUnauthorizedError(SteamApiError):
    pass


class SteamForbiddenError(SteamApiError):
    pass


class SteamRateLimitError(SteamApiError):
    pass


class SteamServerError(SteamApiError):
    pass
