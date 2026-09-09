import json
from decimal import Decimal

import pytest

from app.integrations.amazon.adapter import normalize_search_response
from app.integrations.amazon.client import AmazonCreatorsClient
from app.integrations.amazon.exceptions import AmazonServerError


def make_client():
    return AmazonCreatorsClient(
        client_id="client-id",
        client_secret="secret-value",
        partner_tag="tag-20",
        marketplace="www.amazon.com.br",
        api_base_url="https://creatorsapi.amazon",
        token_url="https://api.amazon.com/auth/o2/token",
    )


def response(payload):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return json.dumps(payload).encode()

    return Response()


def test_amazon_client_caches_token_and_searches(monkeypatch):
    from app.integrations.amazon import client as module

    requests = []

    def fake_urlopen(request, timeout):
        requests.append(request)
        if request.full_url.endswith("/token"):
            return response({"access_token": "access-value", "expires_in": 3600})
        return response({"searchResult": {"items": []}})

    monkeypatch.setattr(module, "urlopen", fake_urlopen)
    api = make_client()

    api.search_items("notebook")
    api.search_items("monitor")

    assert len([req for req in requests if req.full_url.endswith("/token")]) == 1
    assert requests[1].headers["Authorization"] == "Bearer access-value"
    assert requests[1].headers["X-marketplace"] == "www.amazon.com.br"


def test_amazon_normalizes_offer_without_inventing_data():
    payload = {
        "searchResult": {
            "items": [
                {
                    "asin": "B001",
                    "detailPageURL": "https://amazon.test/B001",
                    "itemInfo": {"title": {"displayValue": "Notebook"}},
                    "offersV2": {
                        "listings": [
                            {
                                "price": {
                                    "money": {"amount": 90, "currency": "BRL"},
                                    "savingBasis": {
                                        "money": {"amount": 100, "currency": "BRL"}
                                    },
                                },
                                "merchantInfo": {"id": "seller-1", "name": "Amazon"},
                                "availability": {"type": "InStock"},
                            }
                        ]
                    },
                }
            ]
        }
    }

    item = normalize_search_response(payload)[0]

    assert item.current_price == Decimal("90")
    assert item.original_price == Decimal("100")
    assert item.discount_percent == 10
    assert item.currency == "BRL"
    assert item.seller_external_id == "seller-1"


def test_amazon_skips_item_without_required_identity_fields():
    payload = {
        "searchResult": {
            "items": [
                {
                    "asin": None,
                    "detailPageURL": "https://amazon.test",
                    "itemInfo": {"title": {"displayValue": "Product"}},
                }
            ]
        }
    }
    assert normalize_search_response(payload) == []


def test_amazon_missing_price_remains_unknown():
    payload = {
        "searchResult": {
            "items": [
                {
                    "asin": "B002",
                    "detailPageURL": "https://amazon.test/B002",
                    "itemInfo": {"title": {"displayValue": "Product"}},
                }
            ]
        }
    }
    item = normalize_search_response(payload)[0]
    assert item.current_price is None
    assert item.original_price is None
    assert item.currency is None


def test_amazon_secret_never_appears_in_api_error(monkeypatch):
    from app.integrations.amazon import client as module

    def fail(request, timeout):
        raise TimeoutError("network")

    monkeypatch.setattr(module, "urlopen", fail)
    with pytest.raises(AmazonServerError) as error:
        make_client().search_items("notebook")

    assert "secret-value" not in str(error.value)


def test_amazon_service_reuses_shared_client(monkeypatch):
    from app.core.config import settings
    from app.integrations.amazon import service

    monkeypatch.setattr(settings, "amazon_creators_client_id", "client-id")
    monkeypatch.setattr(settings, "amazon_creators_client_secret", "secret-value")
    monkeypatch.setattr(settings, "amazon_creators_partner_tag", "tag-20")
    service._shared_client.cache_clear()

    assert service._build_client() is service._build_client()
    service._shared_client.cache_clear()