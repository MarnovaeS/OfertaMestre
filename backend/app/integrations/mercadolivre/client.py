import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.integrations.mercadolivre import TOKEN_URL, USER_AGENT
from app.integrations.mercadolivre.exceptions import (
    MercadoLivreAuthorizationRevokedError,
    MercadoLivreOAuthError,
)
from app.integrations.mercadolivre.oauth import MercadoLivreOAuthSettings


class MercadoLivreHttpClient:
    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def exchange_authorization_code(
        self,
        config: MercadoLivreOAuthSettings,
        code: str,
        code_verifier: str,
    ) -> dict[str, Any]:
        return self._post_form(
            {
                "grant_type": "authorization_code",
                "client_id": config.client_id,
                "client_secret": config.client_secret,
                "code": code,
                "redirect_uri": config.redirect_uri,
                "code_verifier": code_verifier,
            }
        )

    def refresh_access_token(
        self,
        config: MercadoLivreOAuthSettings,
        refresh_token: str,
    ) -> dict[str, Any]:
        return self._post_form(
            {
                "grant_type": "refresh_token",
                "client_id": config.client_id,
                "client_secret": config.client_secret,
                "refresh_token": refresh_token,
            }
        )

    def _post_form(self, form: dict[str, str]) -> dict[str, Any]:
        payload = urlencode(form).encode("utf-8")
        request = Request(
            TOKEN_URL,
            data=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": USER_AGENT,
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            self._raise_http_error(exc)
        except URLError as exc:
            raise MercadoLivreOAuthError("Mercado Livre OAuth service is unavailable") from exc

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise MercadoLivreOAuthError("Mercado Livre returned an invalid OAuth response") from exc

        if not isinstance(parsed, dict):
            raise MercadoLivreOAuthError("Mercado Livre returned an invalid OAuth response")
        return parsed

    def _raise_http_error(self, exc: HTTPError) -> None:
        detail = "Mercado Livre rejected the OAuth request"
        try:
            body = exc.read().decode("utf-8")
            parsed = json.loads(body)
            if isinstance(parsed, dict) and parsed.get("error"):
                detail = str(parsed["error"])
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

        if exc.code in {400, 401} and detail in {"invalid_grant", "unauthorized_client"}:
            raise MercadoLivreAuthorizationRevokedError("Mercado Livre authorization is no longer valid") from exc
        raise MercadoLivreOAuthError(detail) from exc
