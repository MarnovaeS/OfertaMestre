import json
import random
import time
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.integrations.steam import USER_AGENT
from app.integrations.steam.exceptions import (
    SteamApiError,
    SteamForbiddenError,
    SteamRateLimitError,
    SteamServerError,
    SteamUnauthorizedError,
)

API_BASE_URL = "https://partner.steam-api.com"
GET_APP_LIST_PATH = "/IStoreService/GetAppList/v1/"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class SteamStoreClient:
    def __init__(self, api_key: str, timeout: float = 10.0, max_retries: int = 2, backoff_base_seconds: float = 0.25) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds

    def get_app_list(
        self,
        *,
        max_results: int,
        last_appid: int | None = None,
        if_modified_since: int | None = None,
        include_games: bool = True,
        include_dlc: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, str | int] = {
            "key": self.api_key,
            "max_results": max_results,
            "include_games": str(include_games).lower(),
            "include_dlc": str(include_dlc).lower(),
        }
        if last_appid is not None:
            params["last_appid"] = last_appid
        if if_modified_since is not None:
            params["if_modified_since"] = if_modified_since
        return self._get_json(GET_APP_LIST_PATH, params)

    def _get_json(self, path: str, params: dict[str, str | int]) -> dict[str, Any]:
        url = f"{API_BASE_URL}{path}?{urlencode(params)}"
        for attempt in range(self.max_retries + 1):
            request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT}, method="GET")
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    parsed = self._parse_json_body(response.read().decode("utf-8"))
                    if not isinstance(parsed, dict):
                        raise SteamApiError("Steam returned an unexpected response")
                    return parsed
            except HTTPError as exc:
                if exc.code in RETRYABLE_STATUS_CODES and attempt < self.max_retries:
                    self._sleep_before_retry(exc, attempt)
                    continue
                self._raise_http_error(exc)
            except URLError as exc:
                raise SteamApiError("Steam API is unavailable") from exc
        raise SteamApiError("Steam API request failed")

    def _parse_json_body(self, body: str) -> Any:
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise SteamApiError("Steam returned invalid JSON") from exc

    def _raise_http_error(self, exc: HTTPError) -> None:
        if exc.code == 401:
            raise SteamUnauthorizedError("Steam API authorization failed") from exc
        if exc.code == 403:
            raise SteamForbiddenError("Steam API access is forbidden") from exc
        if exc.code == 429:
            raise SteamRateLimitError("Steam API rate limit exceeded") from exc
        if 500 <= exc.code <= 599:
            raise SteamServerError("Steam API is temporarily unavailable") from exc
        raise SteamApiError("Steam API request failed") from exc

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
                return max(0.0, (parsedate_to_datetime(header).timestamp() - time.time()))
            except (TypeError, ValueError):
                return None
