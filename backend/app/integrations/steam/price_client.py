from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from decimal import Decimal
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
)

STORE_BASE_URL = "https://store.steampowered.com"
APPDETAILS_PATH = "/api/appdetails"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
PRICE_SOURCE = "store_appdetails"
PRICE_SOURCE_CLASS = "undocumented_public"
COUNTRY_CURRENCY = {"br": "BRL"}


@dataclass(frozen=True)
class SteamPrice:
    appid: int
    currency: str
    current_price: Decimal
    original_price: Decimal | None
    discount_percent: int
    price_source: str = PRICE_SOURCE
    price_source_class: str = PRICE_SOURCE_CLASS
    is_free: bool = False


class SteamPriceUnavailableError(SteamApiError):
    pass


class SteamStorePriceClient:
    def __init__(
        self,
        *,
        base_url: str = STORE_BASE_URL,
        timeout: float = 10.0,
        max_retries: int = 2,
        backoff_base_seconds: float = 0.25,
        min_interval_seconds: float = 0.2,
        circuit_breaker_failures: int = 3,
        circuit_breaker_cooldown_seconds: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds
        self.min_interval_seconds = min_interval_seconds
        self.circuit_breaker_failures = circuit_breaker_failures
        self.circuit_breaker_cooldown_seconds = circuit_breaker_cooldown_seconds
        self._cache: dict[tuple[int, str], SteamPrice] = {}
        self._last_request_at = 0.0
        self._failure_count = 0
        self._degraded_until = 0.0

    def get_price(self, appid: int, *, country_code: str) -> SteamPrice:
        country = country_code.lower()
        cache_key = (appid, country)
        if cache_key in self._cache:
            return self._cache[cache_key]
        if self._is_degraded():
            raise SteamPriceUnavailableError("Steam appdetails price provider is degraded")

        payload = self._get_appdetails(appid, country)
        price = parse_appdetails_price(appid, payload, country_code=country)
        self._cache[cache_key] = price
        self._failure_count = 0
        return price

    def _get_appdetails(self, appid: int, country_code: str) -> dict[str, Any]:
        params = {"appids": appid, "cc": country_code, "filters": "price_overview"}
        url = f"{self.base_url}{APPDETAILS_PATH}?{urlencode(params)}"
        for attempt in range(self.max_retries + 1):
            self._wait_for_local_rate_limit()
            request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT}, method="GET")
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    parsed = self._parse_json_body(response.read().decode("utf-8"))
                    if not isinstance(parsed, dict):
                        raise SteamApiError("Steam appdetails returned an unexpected response")
                    return parsed
            except HTTPError as exc:
                if exc.code in RETRYABLE_STATUS_CODES and attempt < self.max_retries:
                    self._sleep_before_retry(exc, attempt)
                    continue
                self._record_failure(exc.code)
                self._raise_http_error(exc)
            except URLError as exc:
                self._record_failure(0)
                raise SteamApiError("Steam appdetails is unavailable") from exc
        self._record_failure(0)
        raise SteamApiError("Steam appdetails request failed")

    def _parse_json_body(self, body: str) -> Any:
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise SteamApiError("Steam appdetails returned invalid JSON") from exc

    def _raise_http_error(self, exc: HTTPError) -> None:
        if exc.code == 403:
            raise SteamForbiddenError("Steam appdetails access is forbidden") from exc
        if exc.code == 429:
            raise SteamRateLimitError("Steam appdetails rate limit exceeded") from exc
        if 500 <= exc.code <= 599:
            raise SteamServerError("Steam appdetails is temporarily unavailable") from exc
        raise SteamApiError("Steam appdetails request failed") from exc

    def _wait_for_local_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.min_interval_seconds:
            time.sleep(self.min_interval_seconds - elapsed)
        self._last_request_at = time.monotonic()

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

    def _record_failure(self, status_code: int) -> None:
        if status_code in {0, 403, 429, 500, 502, 503, 504}:
            self._failure_count += 1
        if self._failure_count >= self.circuit_breaker_failures:
            self._degraded_until = time.monotonic() + self.circuit_breaker_cooldown_seconds

    def _is_degraded(self) -> bool:
        return time.monotonic() < self._degraded_until


def parse_appdetails_price(appid: int, payload: dict[str, Any], *, country_code: str) -> SteamPrice:
    app_payload = payload.get(str(appid))
    if not isinstance(app_payload, dict):
        raise SteamPriceUnavailableError("Steam appdetails response is missing app payload")
    if app_payload.get("success") is False:
        raise SteamPriceUnavailableError("Steam appdetails returned success=false")
    data = app_payload.get("data") if isinstance(app_payload.get("data"), dict) else {}
    price_overview = data.get("price_overview") if isinstance(data.get("price_overview"), dict) else None
    if price_overview is None:
        if data.get("is_free") is True:
            return SteamPrice(
                appid=appid,
                currency=COUNTRY_CURRENCY.get(country_code.lower(), country_code.upper()),
                current_price=Decimal("0.00"),
                original_price=Decimal("0.00"),
                discount_percent=0,
                is_free=True,
            )
        raise SteamPriceUnavailableError("Steam appdetails price_overview is unavailable")

    currency = _required_str(price_overview.get("currency"), "currency")
    current = _minor_units_to_decimal(price_overview.get("final"), "final")
    original = _minor_units_to_decimal(price_overview.get("initial"), "initial")
    discount_percent = _optional_int(price_overview.get("discount_percent")) or 0

    if original is not None and original < current:
        raise SteamPriceUnavailableError("Steam appdetails original price is lower than current price")
    if not 0 <= discount_percent <= 100:
        raise SteamPriceUnavailableError("Steam appdetails discount_percent is invalid")
    if discount_percent > 0 and original is not None and original == current:
        raise SteamPriceUnavailableError("Steam appdetails discount_percent is inconsistent with prices")

    return SteamPrice(
        appid=appid,
        currency=currency,
        current_price=current,
        original_price=original,
        discount_percent=discount_percent,
    )


def _minor_units_to_decimal(value: Any, field_name: str) -> Decimal:
    if value is None or isinstance(value, bool):
        raise SteamPriceUnavailableError(f"Steam appdetails field '{field_name}' is required")
    try:
        minor_units = Decimal(str(value))
    except Exception as exc:
        raise SteamPriceUnavailableError(f"Steam appdetails field '{field_name}' must be an integer minor-unit amount") from exc
    if minor_units != minor_units.to_integral_value():
        raise SteamPriceUnavailableError(f"Steam appdetails field '{field_name}' must be an integer minor-unit amount")
    if minor_units < 0:
        raise SteamPriceUnavailableError(f"Steam appdetails field '{field_name}' must be non-negative")
    return (minor_units / Decimal("100")).quantize(Decimal("0.01"))


def _required_str(value: Any, field_name: str) -> str:
    if value is None or str(value).strip() == "":
        raise SteamPriceUnavailableError(f"Steam appdetails field '{field_name}' is required")
    return str(value).strip().upper()


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
