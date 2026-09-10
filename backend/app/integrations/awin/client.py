import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.integrations.awin.exceptions import (
    AwinApiError,
    AwinForbiddenError,
    AwinRateLimitError,
    AwinServerError,
    AwinUnauthorizedError,
)


class AwinPublisherClient:
    def __init__(self, *, publisher_id: str, api_token: str, api_base_url: str, timeout: float = 15) -> None:
        self.publisher_id = publisher_id
        self.api_token = api_token
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout = timeout

    def get_programs(self, *, country_code: str = "BR", relationship: str = "joined") -> object:
        query = urlencode({"countryCode": country_code, "relationship": relationship})
        return self._request_json(
            "GET",
            f"{self.api_base_url}/publishers/{self.publisher_id}/programmes?{query}",
        )

    def get_promotions(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        membership: str = "joined",
        status: str = "active",
        promotion_type: str = "all",
        region_code: str = "BR",
        advertiser_id: int | None = None,
    ) -> object:
        filters: dict[str, object] = {
            "membership": membership,
            "status": status,
            "type": promotion_type,
            "regionCodes": [region_code],
        }
        if advertiser_id is not None:
            filters["advertiserIds"] = [advertiser_id]
        payload = {"filters": filters, "pagination": {"page": page, "pageSize": page_size}}
        return self._request_json(
            "POST",
            f"{self.api_base_url}/publisher/{self.publisher_id}/promotions",
            payload,
        )

    def _request_json(self, method: str, url: str, payload: dict | None = None) -> object:
        headers = {"Accept": "application/json", "Authorization": f"Bearer {self.api_token}"}
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode()
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read())
        except HTTPError as exc:
            if exc.code == 401:
                raise AwinUnauthorizedError("Awin rejected the configured API token") from exc
            if exc.code == 403:
                raise AwinForbiddenError("Awin access is forbidden for this publisher account") from exc
            if exc.code == 429:
                raise AwinRateLimitError("Awin API rate limit was reached") from exc
            if exc.code >= 500:
                raise AwinServerError("Awin API is temporarily unavailable") from exc
            raise AwinApiError("Awin API request failed") from exc
        except (URLError, TimeoutError) as exc:
            raise AwinServerError("Awin API is temporarily unavailable") from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise AwinApiError("Awin API returned an invalid JSON response") from exc
