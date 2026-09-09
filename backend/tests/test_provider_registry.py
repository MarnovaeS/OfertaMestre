from app.database.session import SessionLocal
from app.models.store import Store


def auth_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "providers@example.com",
            "full_name": "Provider User",
            "password": "strong-password",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "providers@example.com", "password": "strong-password"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_provider_registry_requires_authentication(client):
    assert client.get("/api/v1/integrations/providers").status_code == 401


def test_provider_registry_lists_requested_stores(client):
    response = client.get("/api/v1/integrations/providers", headers=auth_headers(client))

    assert response.status_code == 200
    providers = {entry["provider"] for entry in response.json()}
    assert {
        "steam",
        "amazon",
        "magalu",
        "casas-bahia",
        "centauro",
        "nike",
        "adidas",
        "havan",
        "shopee",
    } <= providers


def test_provider_registry_reports_store_and_configuration(client, monkeypatch):
    from app.core.config import settings

    headers = auth_headers(client)
    monkeypatch.setattr(settings, "steam_web_api_key", "configured-key")
    with SessionLocal() as db:
        db.add(
            Store(
                name="Steam",
                slug="steam",
                base_url="https://store.steampowered.com",
                is_active=True,
            )
        )
        db.commit()

    payload = client.get("/api/v1/integrations/providers", headers=headers).json()
    steam = next(entry for entry in payload if entry["provider"] == "steam")

    assert steam["configured"] is True
    assert steam["store_exists"] is True
    assert steam["state"] == "configured"


def test_provider_registry_never_returns_secrets(client, monkeypatch):
    from app.core.config import settings

    secret = "never-return-this-secret"
    monkeypatch.setattr(settings, "amazon_creators_client_secret", secret)
    response = client.get(
        "/api/v1/integrations/providers",
        headers=auth_headers(client),
    )

    assert secret not in response.text


def test_registry_uses_canonical_ml_slug_and_no_store_for_awin(client):
    headers = auth_headers(client)
    with SessionLocal() as db:
        db.add(
            Store(
                name="Mercado Livre",
                slug="mercadolivre",
                base_url="https://www.mercadolivre.com.br",
                is_active=True,
            )
        )
        db.commit()

    payload = client.get("/api/v1/integrations/providers", headers=headers).json()
    ml = next(entry for entry in payload if entry["provider"] == "mercadolivre")
    awin = next(entry for entry in payload if entry["provider"] == "awin")

    assert ml["store_slug"] == "mercadolivre"
    assert ml["store_exists"] is True
    assert awin["store_slug"] is None
    assert awin["store_exists"] is None
