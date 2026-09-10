import json
from urllib.error import HTTPError

import pytest

from app.integrations.awin.adapter import normalize_programs, normalize_promotions
from app.integrations.awin.client import AwinPublisherClient
from app.integrations.awin.exceptions import AwinForbiddenError


def make_client() -> AwinPublisherClient:
    return AwinPublisherClient(
        publisher_id="12345",
        api_token="secret-api-token",
        api_base_url="https://api.awin.com",
    )


def response(payload: object):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return json.dumps(payload).encode()

    return Response()


def auth_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "awin@example.com",
            "full_name": "Awin User",
            "password": "strong-password",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "awin@example.com", "password": "strong-password"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_awin_client_lists_programs_with_bearer_token(monkeypatch):
    from app.integrations.awin import client as module

    requests = []

    def fake_urlopen(request, timeout):
        requests.append(request)
        return response([])

    monkeypatch.setattr(module, "urlopen", fake_urlopen)
    make_client().get_programs(country_code="BR", relationship="joined")

    request = requests[0]
    assert request.method == "GET"
    assert request.full_url == (
        "https://api.awin.com/publishers/12345/programmes?countryCode=BR&relationship=joined"
    )
    assert request.headers["Authorization"] == "Bearer secret-api-token"
    assert "secret-api-token" not in request.full_url


def test_awin_client_retrieves_promotions_with_bounded_payload(monkeypatch):
    from app.integrations.awin import client as module

    requests = []

    def fake_urlopen(request, timeout):
        requests.append(request)
        return response({"data": []})

    monkeypatch.setattr(module, "urlopen", fake_urlopen)
    make_client().get_promotions(
        page=2,
        page_size=25,
        membership="joined",
        status="active",
        promotion_type="all",
        region_code="BR",
        advertiser_id=99,
    )

    request = requests[0]
    payload = json.loads(request.data)
    assert request.method == "POST"
    assert request.full_url == "https://api.awin.com/publisher/12345/promotions"
    assert payload["pagination"] == {"page": 2, "pageSize": 25}
    assert payload["filters"] == {
        "membership": "joined",
        "status": "active",
        "type": "all",
        "regionCodes": ["BR"],
        "advertiserIds": [99],
    }


def test_awin_normalizes_programs_without_stringifying_missing_values():
    programs = normalize_programs(
        [
            {
                "id": 99,
                "name": "Loja Exemplo",
                "currencyCode": None,
                "primaryRegion": {"name": "Brazil", "countryCode": "BR"},
            },
            {"id": None, "name": "Registro invalido"},
        ]
    )

    assert len(programs) == 1
    assert programs[0].advertiser_id == 99
    assert programs[0].currency is None
    assert programs[0].primary_region is not None
    assert programs[0].primary_region.country_code == "BR"
    assert "None" not in programs[0].model_dump_json()


def test_awin_rejects_fractional_identifiers_during_normalization():
    assert normalize_programs([{"id": 99.5, "name": "Invalid"}]) == []


def test_awin_normalizes_promotions_and_preserves_unknown_voucher():
    promotions = normalize_promotions(
        {
            "data": [
                {
                    "promotionId": 7,
                    "type": "voucher",
                    "title": "Oferta",
                    "advertiser": {"id": 99, "name": "Loja Exemplo", "joined": False},
                    "voucher": {"code": None},
                }
            ]
        }
    )

    assert len(promotions) == 1
    assert promotions[0].voucher_code is None
    assert promotions[0].advertiser is not None
    assert promotions[0].advertiser.joined is False


def test_awin_errors_never_expose_api_token(monkeypatch):
    from app.integrations.awin import client as module

    def fail(request, timeout):
        raise HTTPError(request.full_url, 403, "secret-api-token", hdrs=None, fp=None)

    monkeypatch.setattr(module, "urlopen", fail)
    with pytest.raises(AwinForbiddenError) as error:
        make_client().get_programs()

    assert "secret-api-token" not in str(error.value)


def test_awin_routes_require_authentication(client):
    assert client.get("/api/v1/integrations/awin/status").status_code == 401
    assert client.get("/api/v1/integrations/awin/programs").status_code == 401
    assert client.get("/api/v1/integrations/awin/promotions").status_code == 401


def test_awin_status_never_returns_token(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "awin_publisher_id", "12345")
    monkeypatch.setattr(settings, "awin_api_token", "secret-api-token")
    result = client.get("/api/v1/integrations/awin/status", headers=auth_headers(client))

    assert result.status_code == 200
    assert result.json() == {"provider": "awin", "configured": True, "publisher_id": "12345"}
    assert "secret-api-token" not in result.text


def test_awin_programs_report_missing_configuration(client, monkeypatch):
    from app.core.config import settings
    from app.integrations.awin import service

    monkeypatch.setattr(settings, "awin_publisher_id", "")
    monkeypatch.setattr(settings, "awin_api_token", "")
    service._shared_client.cache_clear()
    result = client.get("/api/v1/integrations/awin/programs", headers=auth_headers(client))

    assert result.status_code == 503
    assert result.json()["detail"] == "Awin publisher ID and API token are not configured correctly"
