import importlib.util
import json
import subprocess
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest
import sqlalchemy as sa

from app.database.session import SessionLocal
from app.integrations.steam.client import SteamStoreClient
from app.models.price_snapshot import PriceSnapshot
from app.models.provider_catalog_item import ProviderCatalogItem
from app.models.provider_sync_state import ProviderSyncState
from app.models.store import Store
from app.providers.change_detection import has_app_changed
from app.providers.contracts import CatalogItem

STEAM_KEY = "test-steam-key"


def auth_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "steam@example.com", "full_name": "Steam User", "password": "strong-password"},
    )
    response = client.post("/api/v1/auth/login", data={"username": "steam@example.com", "password": "strong-password"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture(autouse=True)
def steam_settings(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "steam_web_api_key", STEAM_KEY)


def create_steam_store():
    with SessionLocal() as db:
        db.add(Store(name="Steam", slug="steam", base_url="https://store.steampowered.com", is_active=True))
        db.commit()


def db_count(model):
    with SessionLocal() as db:
        return db.query(model).count()


def fake_response(apps):
    return {"response": {"apps": apps}}


class FakeSteamClient:
    def __init__(self, apps=None):
        self.apps = apps or [
            {"appid": 10, "name": "Counter-Strike", "last_modified": 100, "price_change_number": 7}
        ]
        self.calls = []

    def get_app_list(self, **kwargs):
        self.calls.append(kwargs)
        return fake_response(self.apps)


def install_fake_steam_client(monkeypatch, fake):
    monkeypatch.setattr("app.integrations.steam.service.SteamStoreClient", lambda key: fake)


def test_get_app_list_valid(monkeypatch):
    from app.integrations.steam import client as client_module

    def ok(request, timeout):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps(fake_response([{"appid": 10, "name": "Counter-Strike"}])).encode()

        return Response()

    monkeypatch.setattr(client_module, "urlopen", ok)

    response = SteamStoreClient(STEAM_KEY).get_app_list(max_results=1)

    assert response["response"]["apps"][0]["appid"] == 10


def test_get_app_list_uses_last_appid(monkeypatch):
    from app.integrations.steam import client as client_module

    seen = {}

    def ok(request, timeout):
        seen["url"] = request.full_url

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return b'{"response":{"apps":[]}}'

        return Response()

    monkeypatch.setattr(client_module, "urlopen", ok)

    SteamStoreClient(STEAM_KEY).get_app_list(max_results=25, last_appid=123)

    assert "last_appid=123" in seen["url"]


def test_apps_endpoint_passes_max_results_and_if_modified_since(client, monkeypatch):
    headers = auth_headers(client)
    fake = FakeSteamClient()
    install_fake_steam_client(monkeypatch, fake)

    response = client.get("/api/v1/integrations/steam/apps?max_results=50&modified_since=123", headers=headers)

    assert response.status_code == 200
    assert fake.calls[0]["max_results"] == 50
    assert fake.calls[0]["if_modified_since"] == 123


def test_appid_and_name_are_normalized(client, monkeypatch):
    headers = auth_headers(client)
    install_fake_steam_client(monkeypatch, FakeSteamClient(apps=[{"appid": "20", "name": " Team Fortress 2 "}]))

    response = client.get("/api/v1/integrations/steam/apps?max_results=1", headers=headers)

    assert response.status_code == 200
    assert response.json() == [{"appid": 20, "name": "Team Fortress 2", "last_modified": None, "price_change_number": None}]


def test_sync_persists_last_modified(client, monkeypatch):
    headers = auth_headers(client)
    create_steam_store()
    install_fake_steam_client(monkeypatch, FakeSteamClient(apps=[{"appid": 30, "name": "Portal", "last_modified": 200}]))

    response = client.post("/api/v1/integrations/steam/sync?max_results=1", headers=headers)

    assert response.status_code == 200
    with SessionLocal() as db:
        item = db.query(ProviderCatalogItem).filter_by(provider="steam", external_id="30").one()
        state = db.query(ProviderSyncState).filter_by(provider="steam").one()
    assert item.last_modified == 200
    assert state.metadata_json["last_modified"] == 200


def test_sync_persists_price_change_number(client, monkeypatch):
    headers = auth_headers(client)
    create_steam_store()
    install_fake_steam_client(monkeypatch, FakeSteamClient(apps=[{"appid": 40, "name": "Half-Life", "price_change_number": 9}]))

    client.post("/api/v1/integrations/steam/sync?max_results=1", headers=headers)

    with SessionLocal() as db:
        item = db.query(ProviderCatalogItem).filter_by(provider="steam", external_id="40").one()
    assert item.price_change_number == 9


def test_price_change_number_changed_signals_change():
    previous = CatalogItem(provider="steam", external_id="50", name="Game", price_change_number=1)
    current = CatalogItem(provider="steam", external_id="50", name="Game", price_change_number=2)

    assert has_app_changed(previous, current) is True


def test_identical_sync_is_idempotent(client, monkeypatch):
    headers = auth_headers(client)
    create_steam_store()
    fake = FakeSteamClient(apps=[{"appid": 60, "name": "Dota 2", "last_modified": 300, "price_change_number": 1}])
    install_fake_steam_client(monkeypatch, fake)

    first = client.post("/api/v1/integrations/steam/sync?max_results=1", headers=headers).json()
    second = client.post("/api/v1/integrations/steam/sync?max_results=1", headers=headers).json()

    assert first["catalog_items_created"] == 1
    assert second["catalog_items_created"] == 0
    assert second["catalog_items_updated"] == 0
    assert db_count(ProviderCatalogItem) == 1


def test_missing_api_key_returns_invalid_configuration(client, monkeypatch):
    from app.core.config import settings

    headers = auth_headers(client)
    monkeypatch.setattr(settings, "steam_web_api_key", None)

    response = client.get("/api/v1/integrations/steam/apps?max_results=1", headers=headers)

    assert response.status_code == 503
    assert response.json()["detail"] == "STEAM_WEB_API_KEY is not configured"


def test_api_key_never_appears_in_response_or_logs(client, monkeypatch, caplog):
    headers = auth_headers(client)
    install_fake_steam_client(monkeypatch, FakeSteamClient())

    response = client.get("/api/v1/integrations/steam/apps?max_results=1", headers=headers)

    assert response.status_code == 200
    assert STEAM_KEY not in response.text
    assert STEAM_KEY not in caplog.text


def test_429_applies_limited_retry(monkeypatch):
    from app.integrations.steam import client as client_module

    calls = {"count": 0}

    def raise_429(request, timeout):
        calls["count"] += 1
        raise HTTPError(request.full_url, 429, "Too Many Requests", Message(), None)

    monkeypatch.setattr(client_module, "urlopen", raise_429)
    monkeypatch.setattr(client_module.time, "sleep", lambda seconds: None)

    with pytest.raises(Exception):
        SteamStoreClient(STEAM_KEY, max_retries=2, backoff_base_seconds=0).get_app_list(max_results=1)

    assert calls["count"] == 3


def test_5xx_applies_limited_retry(monkeypatch):
    from app.integrations.steam import client as client_module

    calls = {"count": 0}

    def raise_500(request, timeout):
        calls["count"] += 1
        raise HTTPError(request.full_url, 500, "Server Error", Message(), None)

    monkeypatch.setattr(client_module, "urlopen", raise_500)
    monkeypatch.setattr(client_module.time, "sleep", lambda seconds: None)

    with pytest.raises(Exception):
        SteamStoreClient(STEAM_KEY, max_retries=1, backoff_base_seconds=0).get_app_list(max_results=1)

    assert calls["count"] == 2


def test_4xx_does_not_loop(monkeypatch):
    from app.integrations.steam import client as client_module

    calls = {"count": 0}

    def raise_400(request, timeout):
        calls["count"] += 1
        raise HTTPError(request.full_url, 400, "Bad Request", Message(), None)

    monkeypatch.setattr(client_module, "urlopen", raise_400)

    with pytest.raises(Exception):
        SteamStoreClient(STEAM_KEY, max_retries=2).get_app_list(max_results=1)

    assert calls["count"] == 1


def test_steam_store_exists_after_migration():
    migration = _load_provider_migration()
    engine = _create_store_migration_engine()

    with engine.begin() as connection:
        with _patched_op_bind(migration, connection):
            migration._seed_steam_store()
        store = connection.execute(sa.text("SELECT name, slug, base_url, is_active FROM stores WHERE slug='steam'")).mappings().one()

    assert dict(store) == {
        "name": "Steam",
        "slug": "steam",
        "base_url": "https://store.steampowered.com",
        "is_active": True,
    }


def test_steam_store_migration_is_idempotent():
    migration = _load_provider_migration()
    engine = _create_store_migration_engine()

    with engine.begin() as connection:
        with _patched_op_bind(migration, connection):
            migration._seed_steam_store()
            migration._seed_steam_store()
        count = connection.execute(sa.text("SELECT COUNT(*) FROM stores WHERE slug='steam'")).scalar_one()

    assert count == 1


def test_sync_does_not_create_price_snapshot_without_real_price(client, monkeypatch):
    headers = auth_headers(client)
    create_steam_store()
    install_fake_steam_client(monkeypatch, FakeSteamClient())

    response = client.post("/api/v1/integrations/steam/sync?max_results=1", headers=headers)

    assert response.status_code == 200
    assert response.json()["price_data_available"] is False
    assert response.json()["price_snapshots_created"] == 0
    assert db_count(PriceSnapshot) == 0


def test_mercadolivre_code_is_not_modified():
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--", "backend/app/integrations/mercadolivre", "backend/app/api/routes/mercadolivre.py"],
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == ""


def _load_provider_migration():
    migration_path = Path(__file__).parents[1] / "alembic" / "versions" / "202608090001_create_provider_foundation.py"
    spec = importlib.util.spec_from_file_location("create_provider_foundation", migration_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _create_store_migration_engine():
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                """
                CREATE TABLE stores (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) NOT NULL UNIQUE,
                    base_url VARCHAR(2048) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1
                )
                """
            )
        )
    return engine


class _patched_op_bind:
    def __init__(self, migration, connection):
        self.migration = migration
        self.connection = connection
        self.original = migration.op.get_bind

    def __enter__(self):
        self.migration.op.get_bind = lambda: self.connection

    def __exit__(self, exc_type, exc, traceback):
        self.migration.op.get_bind = self.original
