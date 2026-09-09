import json
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.integrations.amazon.exceptions import (
    AmazonApiError,
    AmazonForbiddenError,
    AmazonRateLimitError,
    AmazonServerError,
    AmazonUnauthorizedError,
)


@dataclass(frozen=True)
class _Token:
    value: str
    expires_at: float


class AmazonCreatorsClient:
    def __init__(self, *, client_id: str, client_secret: str, partner_tag: str, marketplace: str, api_base_url: str, token_url: str, timeout: float = 15) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.partner_tag = partner_tag
        self.marketplace = marketplace
        self.api_base_url = api_base_url.rstrip("/")
        self.token_url = token_url
        self.timeout = timeout
        self._token: _Token | None = None

    def search_items(self, keywords: str, *, item_count: int = 10) -> dict:
        payload = {
            "keywords": keywords,
            "searchIndex": "All",
            "itemCount": item_count,
            "marketplace": self.marketplace,
            "partnerTag": self.partner_tag,
            "resources": [
                "images.primary.medium",
                "itemInfo.title",
                "offersV2.listings.availability",
                "offersV2.listings.merchantInfo",
                "offersV2.listings.price",
            ],
        }
        return self._request_json(
            f"{self.api_base_url}/catalog/v1/searchItems",
            payload,
            {"Authorization": f"Bearer {self._access_token()}", "x-marketplace": self.marketplace},
        )

    def _access_token(self) -> str:
        now = time.monotonic()
        if self._token and self._token.expires_at > now + 30:
            return self._token.value
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "creatorsapi::default",
        }
        response = self._request_json(self.token_url, payload)
        value = response.get("access_token")
        expires_in = response.get("expires_in", 3600)
        if not isinstance(value, str) or not value or not isinstance(expires_in, (int, float)):
            raise AmazonApiError("Amazon Creators API returned an invalid token response")
        self._token = _Token(value=value, expires_at=now + max(float(expires_in), 0))
        return value

    def _request_json(self, url: str, payload: dict, extra_headers: dict[str, str] | None = None) -> dict:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        headers.update(extra_headers or {})
        request = Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                parsed = json.loads(response.read())
        except HTTPError as exc:
            if exc.code == 401:
                raise AmazonUnauthorizedError("Amazon Creators API rejected the configured credentials") from exc
            if exc.code == 403:
                raise AmazonForbiddenError("Amazon Creators API access is forbidden for this account") from exc
            if exc.code == 429:
                raise AmazonRateLimitError("Amazon Creators API rate limit was reached") from exc
            if exc.code >= 500:
                raise AmazonServerError("Amazon Creators API is temporarily unavailable") from exc
            raise AmazonApiError("Amazon Creators API request failed") from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise AmazonServerError("Amazon Creators API is temporarily unavailable") from exc
        if not isinstance(parsed, dict):
            raise AmazonApiError("Amazon Creators API returned an invalid response")
        return parsed
