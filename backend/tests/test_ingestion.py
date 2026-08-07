import pytest

from app.database.session import SessionLocal
from app.models.brand import Brand
from app.models.price_snapshot import PriceSnapshot
from app.models.product import Product
from app.models.product_offer import ProductOffer
from app.models.seller import Seller


def auth_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "ingestion@example.com", "full_name": "Ingestion User", "password": "strong-password"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "ingestion@example.com", "password": "strong-password"},
    )
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def create_store(client, headers, slug="amazon-brasil", name="Amazon Brasil"):
    response = client.post(
        "/api/v1/stores",
        json={"name": name, "slug": slug, "base_url": f"https://{slug}.example.com"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def create_seller(client, headers, store_id, external_id="seller-1", name="Samsung Oficial"):
    response = client.post(
        "/api/v1/sellers",
        json={"store_id": store_id, "name": name, "external_id": external_id, "is_official": True},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def external_offer(**overrides):
    payload = {
        "source": "test-collector",
        "external_id": "offer-1",
        "store_slug": "amazon-brasil",
        "seller_external_id": "seller-1",
        "seller_name": "Samsung Oficial",
        "seller_is_official": True,
        "title": "Galaxy Watch Ultra Samsung Oficial",
        "product_name": "Galaxy Watch Ultra",
        "brand_name": "Samsung",
        "category_name": "Smartwatches",
        "model": "Ultra",
        "gtin": "7891234567890",
        "sku": "WATCH-ULTRA",
        "url": "https://www.amazon.com.br/offer-1",
        "image_url": "https://www.amazon.com.br/offer-1.jpg",
        "current_price": "2199.00",
        "original_price": "2499.00",
        "shipping_price": "0.00",
        "currency": "brl",
        "is_available": True,
        "is_free_shipping": True,
        "is_prime": True,
        "installment_count": 10,
        "installment_value": "219.90",
        "captured_at": "2026-08-07T10:00:00Z",
    }
    payload.update(overrides)
    return payload


def ingest(client, headers, payload):
    return client.post("/api/v1/internal/ingestion/offers", json=payload, headers=headers)


def db_count(model):
    db = SessionLocal()
    try:
        return db.query(model).count()
    finally:
        db.close()


def get_offer(offer_id):
    db = SessionLocal()
    try:
        return db.get(ProductOffer, offer_id)
    finally:
        db.close()


def get_seller(seller_id):
    db = SessionLocal()
    try:
        return db.get(Seller, seller_id)
    finally:
        db.close()


def test_ingests_new_product_offer_and_snapshot(client):
    headers = auth_headers(client)
    create_store(client, headers)

    response = ingest(client, headers, external_offer())

    assert response.status_code == 201
    body = response.json()
    assert body["product_created"] is True
    assert body["offer_created"] is True
    assert body["seller_created"] is True
    assert body["snapshot_created"] is True
    assert body["matched_by"] == "created_new"
    assert db_count(Product) == 1
    assert db_count(ProductOffer) == 1
    assert db_count(PriceSnapshot) == 1


def test_identical_ingestion_is_idempotent(client):
    headers = auth_headers(client)
    create_store(client, headers)
    payload = external_offer()

    first = ingest(client, headers, payload).json()
    second_response = ingest(client, headers, payload)

    assert second_response.status_code == 201
    second = second_response.json()
    assert second["product_id"] == first["product_id"]
    assert second["offer_id"] == first["offer_id"]
    assert second["seller_id"] == first["seller_id"]
    assert second["product_created"] is False
    assert second["offer_created"] is False
    assert second["seller_created"] is False
    assert second["snapshot_created"] is False
    assert db_count(PriceSnapshot) == 1


def test_price_change_creates_new_snapshot(client):
    headers = auth_headers(client)
    create_store(client, headers)
    ingest(client, headers, external_offer())

    response = ingest(client, headers, external_offer(current_price="2099.00", captured_at="2026-08-07T11:00:00Z"))

    assert response.status_code == 201
    assert response.json()["snapshot_created"] is True
    assert db_count(PriceSnapshot) == 2


def test_same_gtin_reuses_product(client):
    headers = auth_headers(client)
    create_store(client, headers)
    first = ingest(client, headers, external_offer(external_id="offer-1")).json()

    second = ingest(
        client,
        headers,
        external_offer(external_id="offer-2", product_name="Galaxy Watch Ultra LTE", sku="DIFFERENT-SKU"),
    ).json()

    assert second["product_id"] == first["product_id"]
    assert second["matched_by"] == "gtin"
    assert db_count(Product) == 1


def test_same_brand_and_model_reuses_product(client):
    headers = auth_headers(client)
    create_store(client, headers)
    base = external_offer(gtin=None, sku=None, external_id="offer-1")
    first = ingest(client, headers, base).json()

    second = ingest(
        client,
        headers,
        external_offer(gtin=None, sku=None, external_id="offer-2", product_name="Samsung Relogio Ultra"),
    ).json()

    assert second["product_id"] == first["product_id"]
    assert second["matched_by"] == "brand_model"
    assert db_count(Product) == 1


def test_existing_offer_updates_mutable_fields(client):
    headers = auth_headers(client)
    create_store(client, headers)
    first = ingest(client, headers, external_offer()).json()

    response = ingest(
        client,
        headers,
        external_offer(title="Galaxy Watch Ultra Atualizado", url="https://www.amazon.com.br/offer-1-updated"),
    )

    assert response.status_code == 201
    assert response.json()["offer_id"] == first["offer_id"]
    assert response.json()["offer_created"] is False
    offer = get_offer(first["offer_id"])
    assert offer.title == "Galaxy Watch Ultra Atualizado"
    assert offer.url == "https://www.amazon.com.br/offer-1-updated"


def test_seller_is_created_in_correct_store(client):
    headers = auth_headers(client)
    store = create_store(client, headers)

    response = ingest(client, headers, external_offer())

    seller = get_seller(response.json()["seller_id"])
    assert seller.store_id == store["id"]


def test_missing_store_returns_404(client):
    headers = auth_headers(client)

    response = ingest(client, headers, external_offer(store_slug="missing-store"))

    assert response.status_code == 404
    assert response.json()["detail"] == "Store not found"


def test_seller_from_another_store_is_not_reused(client):
    headers = auth_headers(client)
    store = create_store(client, headers)
    other_store = create_store(client, headers, slug="mercado-livre", name="Mercado Livre")
    other_seller = create_seller(client, headers, other_store["id"], external_id="seller-1")

    response = ingest(client, headers, external_offer())

    assert response.status_code == 201
    assert response.json()["seller_id"] != other_seller["id"]
    seller = get_seller(response.json()["seller_id"])
    assert seller.store_id == store["id"]


def test_negative_price_is_rejected(client):
    headers = auth_headers(client)
    create_store(client, headers)

    response = ingest(client, headers, external_offer(current_price="-1.00"))

    assert response.status_code == 422


def test_ingestion_failure_rolls_back(client, monkeypatch):
    from app.ingestion import service

    headers = auth_headers(client)
    create_store(client, headers)

    def raise_on_snapshot(**kwargs):
        raise RuntimeError("snapshot failure")

    monkeypatch.setattr(service, "PriceSnapshot", raise_on_snapshot)

    with pytest.raises(RuntimeError):
        ingest(client, headers, external_offer())

    assert db_count(Brand) == 0
    assert db_count(Product) == 0
    assert db_count(ProductOffer) == 0


def test_duplicate_offer_does_not_create_duplicate_product(client):
    headers = auth_headers(client)
    create_store(client, headers)
    ingest(client, headers, external_offer(external_id="same-offer"))

    response = ingest(
        client,
        headers,
        external_offer(external_id="same-offer", product_name="Galaxy Watch Ultra Different Title"),
    )

    assert response.status_code == 201
    assert response.json()["offer_created"] is False
    assert db_count(Product) == 1
