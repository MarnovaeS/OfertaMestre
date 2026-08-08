import json
import random
import time
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.integrations.mercadolivre import TOKEN_URL, USER_AGENT
from app.integrations.mercadolivre.exceptions import (
    MercadoLivreApiError,
    MercadoLivreAuthorizationRevokedError,
    MercadoLivreForbiddenError,
    MercadoLivreNotFoundError,
    MercadoLivreOAuthError,
    MercadoLivreRateLimitError,
    MercadoLivreServerError,
    MercadoLivreUnauthorizedError,
)
from app.integrations.mercadolivre.oauth import MercadoLivreOAuthSettings, now_utc

API_BASE_URL = "https://api.mercadolibre.com"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class MercadoLivreHttpClient:
    def __init__(self, timeout: float = 10.0, max_retries: int = 2, backoff_base_seconds: float = 0.25) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds

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

    def get_item(self, item_id: str, access_token: str) -> dict[str, Any]:
        return self._get_json(f"/items/{item_id}", access_token, operation="item")

    def get_items(self, item_ids: list[str], access_token: str) -> list[dict[str, Any]]:
        if not item_ids:
            return []
        response = self._get_json(f"/items?ids={','.join(item_ids)}", access_token, operation="items")
        return response if isinstance(response, list) else []

    def get_sale_price(self, item_id: str, access_token: str) -> dict[str, Any] | None:
        try:
            return self._get_json(f"/items/{item_id}/sale_price?context=channel_marketplace", access_token, operation="sale_price")
        except MercadoLivreNotFoundError:
            return None

    def get_item_prices(self, item_id: str, access_token: str) -> dict[str, Any] | None:
        try:
            return self._get_json(f"/items/{item_id}/prices", access_token, operation="prices")
        except MercadoLivreNotFoundError:
            return None

    def get_seller(self, seller_id: int | str, access_token: str) -> dict[str, Any]:
        return self._get_json(f"/users/{seller_id}", access_token, operation="seller")

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
            self._raise_oauth_http_error(exc)
        except URLError as exc:
            raise MercadoLivreOAuthError("Mercado Livre OAuth service is unavailable") from exc

        return self._parse_json_body(body)

    def _get_json(self, path: str, access_token: str, *, operation: str) -> Any:
        url = f"{API_BASE_URL}{path}"
        for attempt in range(self.max_retries + 1):
            request = Request(
                url,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {access_token}",
                    "User-Agent": USER_AGENT,
                },
                method="GET",
            )
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    return self._parse_json_body(response.read().decode("utf-8"))
            except HTTPError as exc:
                if exc.code in RETRYABLE_STATUS_CODES and attempt < self.max_retries:
                    self._sleep_before_retry(exc, attempt)
                    continue
                self._raise_api_http_error(exc, operation)
            except URLError as exc:
                raise MercadoLivreApiError("Mercado Livre API is unavailable") from exc
        raise MercadoLivreApiError("Mercado Livre API request failed")

    def _parse_json_body(self, body: str) -> Any:
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise MercadoLivreApiError("Mercado Livre returned an invalid JSON response") from exc

    def _raise_oauth_http_error(self, exc: HTTPError) -> None:
        detail = self._safe_error_detail(exc, "Mercado Livre rejected the OAuth request")
        if exc.code in {400, 401} and detail in {"invalid_grant", "unauthorized_client"}:
            raise MercadoLivreAuthorizationRevokedError("Mercado Livre authorization is no longer valid") from exc
        raise MercadoLivreOAuthError(detail) from exc

    def _raise_api_http_error(self, exc: HTTPError, operation: str) -> None:
        detail = self._safe_error_detail(exc, "Mercado Livre API request failed")
        if exc.code == 401:
            raise MercadoLivreUnauthorizedError("Mercado Livre API authorization failed") from exc
        if exc.code == 403:
            raise MercadoLivreForbiddenError("Mercado Livre API access is forbidden", operation=operation) from exc
        if exc.code == 404:
            raise MercadoLivreNotFoundError("Mercado Livre resource not found") from exc
        if exc.code == 429:
            raise MercadoLivreRateLimitError("Mercado Livre API rate limit exceeded") from exc
        if 500 <= exc.code <= 599:
            raise MercadoLivreServerError("Mercado Livre API is temporarily unavailable") from exc
        raise MercadoLivreApiError(detail) from exc

    def _safe_error_detail(self, exc: HTTPError, fallback: str) -> str:
        try:
            parsed = json.loads(exc.read().decode("utf-8"))
            if isinstance(parsed, dict) and parsed.get("error"):
                return str(parsed["error"])
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        return fallback

    def _sleep_before_retry(self, exc: HTTPError, attempt: int) -> None:
        retry_after = self._retry_after_seconds(exc)
        if retry_after is None:
            retry_after = self.backoff_base_seconds * (2**attempt) + random.uniform(0, self.backoff_base_seconds)
        time.sleep(retry_after)

    def _retry_after_seconds(self, exc: HTTPError) -> float | None:
        header = exc.headers.get("Retry-After") if exc.headers else None
        if not header:
            return None
        try:
            return max(0.0, float(header))
        except ValueError:
            try:
                return max(0.0, (parsedate_to_datetime(header) - now_utc()).total_seconds())
            except (TypeError, ValueError):
                return None
