from datetime import timedelta
from decimal import Decimal
from email.message import Message
from urllib.error import HTTPError

import pytest

from app.database.session import SessionLocal
from app.integrations.mercadolivre.client import MercadoLivreHttpClient
from app.integrations.mercadolivre.oauth import TokenCipher, now_utc
from app.models.oauth_integration import OAuthIntegration
from app.models.price_snapshot import PriceSnapshot
from app.models.product_offer import ProductOffer
from app.models.seller import Seller
from app.models.store import Store

OAUTH_SECRET = "Ma8iYs3Q_SXRriqBjOsJpa91OnP2G854OW_Z1psOtbE="


def auth_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "ml-ingest@example.com", "full_name": "ML User", "password": "strong-password"},
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "ml-ingest@example.com", "password": "strong-password"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def mercadolivre_settings(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "mercadolivre_client_id", "ml-client-id")
    monkeypatch.setattr(settings, "mercadolivre_client_secret", "ml-client-secret")
    monkeypatch.setattr(settings, "mercadolivre_redirect_uri", "https://example.ngrok.dev/oauth/mercadolivre/callback")
    monkeypatch.setattr(settings, "oauth_token_encryption_key", OAUTH_SECRET)


def create_store():
    with SessionLocal() as db:
        store = Store(name="Mercado Livre", slug="mercadolivre", base_url="https://www.mercadolivre.com.br")
        db.add(store)
        db.commit()


def create_oauth_integration(user_id=1):
    cipher = TokenCipher(OAUTH_SECRET)
    with SessionLocal() as db:
        integration = OAuthIntegration(
            user_id=user_id,
            provider="mercadolivre",
            provider_user_id="123456",
            access_token=cipher.encrypt("fake-access-token"),
            refresh_token=cipher.encrypt("fake-refresh-token"),
            token_type="bearer",
            expires_at=now_utc() + timedelta(hours=1),
            scope="offline_access",
            is_active=True,
        )
        db.add(integration)
        db.commit()


def get_user_id():
    with SessionLocal() as db:
        return db.query(OAuthIntegration).first().user_id


def item_payload(**overrides):
    payload = {
        "id": "MLB123456789",
        "title": "Notebook Gamer Acer Nitro 5",
        "seller_id": 998877,
        "category_id": "MLB1648",
        "official_store_id": 123,
        "price": 4200.0,
        "original_price": 4599.0,
        "currency_id": "BRL",
        "available_quantity": 7,
        "status": "active",
        "permalink": "https://www.mercadolivre.com.br/notebook-acer-nitro-5/p/MLB123456789",
        "secure_thumbnail": "https://http2.mlstatic.com/D_NQ_NP_123.jpg",
        "shipping": {"free_shipping": True},
        "installments": {"quantity": 10, "amount": 399.9},
        "attributes": [
            {"id": "BRAND", "value_name": "Acer"},
            {"id": "MODEL", "value_name": "Nitro 5"},
            {"id": "GTIN", "value_name": "7891234567890"},
            {"id": "SELLER_SKU", "value_name": "NITRO-5"},
        ],
    }
    payload.update(overrides)
    return payload


class FakeMercadoLivreClient:
    def __init__(self, item=None, sale_price=None, seller=None, error=None):
        self.item = item or item_payload()
        self.sale_price = sale_price if sale_price is not None else {
            "amount": 3999.0,
            "regular_amount": 4599.0,
            "currency_id": "BRL",
        }
        self.seller = seller or {"id": 998877, "nickname": "Acer Oficial"}
        self.error = error
        self.item_calls = 0
        self.seller_calls = 0

    def get_item(self, item_id, access_token):
        self.item_calls += 1
        assert access_token == "fake-access-token"
        if self.error:
            raise self.error
        return self.item

    def get_sale_price(self, item_id, access_token):
        return self.sale_price

    def get_item_prices(self, item_id, access_token):
        return {"id": item_id, "prices": []}

    def get_seller(self, seller_id, access_token):
        self.seller_calls += 1
        return self.seller


def install_fake_client(monkeypatch, fake):
    monkeypatch.setattr("app.integrations.mercadolivre.collector.MercadoLivreHttpClient", lambda: fake)


def prepare_connected_user(client):
    headers = auth_headers(client)
    create_store()
    create_oauth_integration()
    return headers


def count(model):
    with SessionLocal() as db:
        return db.query(model).count()


def get_offer():
    with SessionLocal() as db:
        return db.query(ProductOffer).first()


def get_seller_name():
    with SessionLocal() as db:
        return db.query(Seller).first().name


def test_valid_item_is_normalized(client, monkeypatch):
    headers = prepare_connected_user(client)
    install_fake_client(monkeypatch, FakeMercadoLivreClient())

    response = client.get("/api/v1/integrations/mercadolivre/items/MLB123456789", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "mercadolivre"
    assert body["external_id"] == "MLB123456789"
    assert body["store_slug"] == "mercadolivre"
    assert body["seller_external_id"] == "998877"
    assert body["seller_name"] == "Acer Oficial"
    assert body["brand_name"] == "Acer"
    assert body["model"] == "Nitro 5"
    assert body["gtin"] == "7891234567890"
    assert body["sku"] == "NITRO-5"
    assert Decimal(body["current_price"]) == Decimal("3999.00")
    assert Decimal(body["original_price"]) == Decimal("4599.00")
    assert Decimal(body["shipping_price"]) == Decimal("0.00")


def test_valid_item_is_ingested(client, monkeypatch):
    headers = prepare_connected_user(client)
    install_fake_client(monkeypatch, FakeMercadoLivreClient())

    response = client.post("/api/v1/integrations/mercadolivre/items/MLB123456789/ingest", headers=headers)

    assert response.status_code == 201
    assert response.json()["product_created"] is True
    assert response.json()["offer_created"] is True
    assert response.json()["snapshot_created"] is True
    assert count(ProductOffer) == 1
    assert count(PriceSnapshot) == 1


def test_identical_second_ingestion_is_idempotent(client, monkeypatch):
    headers = prepare_connected_user(client)
    install_fake_client(monkeypatch, FakeMercadoLivreClient())

    first = client.post("/api/v1/integrations/mercadolivre/items/MLB123456789/ingest", headers=headers).json()
    second = client.post("/api/v1/integrations/mercadolivre/items/MLB123456789/ingest", headers=headers).json()

    assert second["offer_id"] == first["offer_id"]
    assert second["product_created"] is False
    assert second["offer_created"] is False
    assert second["snapshot_created"] is False
    assert count(PriceSnapshot) == 1


def test_price_change_creates_snapshot(client, monkeypatch):
    headers = prepare_connected_user(client)
    fake = FakeMercadoLivreClient()
    install_fake_client(monkeypatch, fake)
    client.post("/api/v1/integrations/mercadolivre/items/MLB123456789/ingest", headers=headers)
    fake.sale_price = {"amount": 3899.0, "regular_amount": 4599.0, "currency_id": "BRL"}

    response = client.post("/api/v1/integrations/mercadolivre/items/MLB123456789/ingest", headers=headers)

    assert response.status_code == 201
    assert response.json()["snapshot_created"] is True
    assert count(PriceSnapshot) == 2


def test_missing_item_returns_404(client, monkeypatch):
    from app.integrations.mercadolivre.exceptions import MercadoLivreNotFoundError

    headers = prepare_connected_user(client)
    install_fake_client(monkeypatch, FakeMercadoLivreClient(error=MercadoLivreNotFoundError("Mercado Livre resource not found")))

    response = client.get("/api/v1/integrations/mercadolivre/items/MLB404", headers=headers)

    assert response.status_code == 404


def test_401_is_handled(client, monkeypatch):
    from app.integrations.mercadolivre.exceptions import MercadoLivreUnauthorizedError

    headers = prepare_connected_user(client)
    install_fake_client(monkeypatch, FakeMercadoLivreClient(error=MercadoLivreUnauthorizedError("Mercado Livre API authorization failed")))

    response = client.get("/api/v1/integrations/mercadolivre/items/MLB123", headers=headers)

    assert response.status_code == 401


def test_429_retries_are_limited(monkeypatch):
    from app.integrations.mercadolivre import client as client_module

    calls = {"count": 0}

    def raise_429(request, timeout):
        calls["count"] += 1
        raise HTTPError(request.full_url, 429, "Too Many Requests", Message(), None)

    monkeypatch.setattr(client_module, "urlopen", raise_429)
    monkeypatch.setattr(client_module.time, "sleep", lambda seconds: None)
    api_client = MercadoLivreHttpClient(max_retries=2, backoff_base_seconds=0)

    with pytest.raises(Exception):
        api_client.get_item("MLB123", "token")

    assert calls["count"] == 3


def test_retry_after_is_respected(monkeypatch):
    from app.integrations.mercadolivre import client as client_module

    sleeps = []
    calls = {"count": 0}
    headers = Message()
    headers["Retry-After"] = "2"

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return b'{"ok": true}'

    def flaky(request, timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            raise HTTPError(request.full_url, 429, "Too Many Requests", headers, None)
        return Response()

    monkeypatch.setattr(client_module, "urlopen", flaky)
    monkeypatch.setattr(client_module.time, "sleep", lambda seconds: sleeps.append(seconds))

    assert MercadoLivreHttpClient(max_retries=1).get_item("MLB123", "token") == {"ok": True}
    assert sleeps == [2.0]


def test_5xx_does_not_loop_forever(monkeypatch):
    from app.integrations.mercadolivre import client as client_module

    calls = {"count": 0}

    def raise_500(request, timeout):
        calls["count"] += 1
        raise HTTPError(request.full_url, 500, "Server Error", Message(), None)

    monkeypatch.setattr(client_module, "urlopen", raise_500)
    monkeypatch.setattr(client_module.time, "sleep", lambda seconds: None)

    with pytest.raises(Exception):
        MercadoLivreHttpClient(max_retries=1, backoff_base_seconds=0).get_item("MLB123", "token")

    assert calls["count"] == 2


def test_seller_is_mapped_correctly(client, monkeypatch):
    headers = prepare_connected_user(client)
    fake = FakeMercadoLivreClient(seller={"id": 998877, "nickname": "Loja Oficial Acer"})
    install_fake_client(monkeypatch, fake)

    response = client.post("/api/v1/integrations/mercadolivre/items/MLB123456789/ingest", headers=headers)

    assert response.status_code == 201
    assert response.json()["seller_created"] is True
    assert fake.seller_calls == 1
    assert get_seller_name() == "Loja Oficial Acer"


def test_missing_mercadolivre_store_returns_clear_error(client, monkeypatch):
    headers = auth_headers(client)
    create_oauth_integration()
    install_fake_client(monkeypatch, FakeMercadoLivreClient())

    response = client.get("/api/v1/integrations/mercadolivre/items/MLB123456789", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Store mercadolivre not found"


def test_tokens_never_appear_in_response_or_logs(client, monkeypatch, caplog):
    headers = prepare_connected_user(client)
    install_fake_client(monkeypatch, FakeMercadoLivreClient())

    response = client.get("/api/v1/integrations/mercadolivre/items/MLB123456789", headers=headers)

    assert response.status_code == 200
    assert "fake-access-token" not in response.text
    assert "fake-refresh-token" not in response.text
    assert "fake-access-token" not in caplog.text
    assert "fake-refresh-token" not in caplog.text


def test_incomplete_optional_api_response_does_not_break_normalization(client, monkeypatch):
    headers = prepare_connected_user(client)
    incomplete = item_payload(attributes=[], shipping={}, installments={}, secure_thumbnail=None)
    install_fake_client(monkeypatch, FakeMercadoLivreClient(item=incomplete, seller=None))

    response = client.get("/api/v1/integrations/mercadolivre/items/MLB123456789", headers=headers)

    assert response.status_code == 200
    assert response.json()["brand_name"] is None
    assert response.json()["shipping_price"] is None


def test_invalid_price_is_rejected(client, monkeypatch):
    headers = prepare_connected_user(client)
    install_fake_client(monkeypatch, FakeMercadoLivreClient(sale_price={"amount": -1, "currency_id": "BRL"}))

    response = client.post("/api/v1/integrations/mercadolivre/items/MLB123456789/ingest", headers=headers)

    assert response.status_code == 422


def test_unavailable_item_is_persisted(client, monkeypatch):
    headers = prepare_connected_user(client)
    unavailable = item_payload(status="paused", available_quantity=0)
    install_fake_client(monkeypatch, FakeMercadoLivreClient(item=unavailable))

    response = client.post("/api/v1/integrations/mercadolivre/items/MLB123456789/ingest", headers=headers)

    assert response.status_code == 201
    offer = get_offer()
    assert offer.is_available is False
