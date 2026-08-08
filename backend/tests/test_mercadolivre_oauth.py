from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest

from app.database.session import SessionLocal
from app.integrations.mercadolivre import AUTHORIZATION_URL, PROVIDER
from app.integrations.mercadolivre.exceptions import MercadoLivreAuthorizationRevokedError
from app.integrations.mercadolivre.oauth import TokenCipher, build_code_challenge, now_utc
from app.integrations.mercadolivre.service import get_valid_access_token
from app.models.oauth_integration import OAuthIntegration
from app.models.oauth_state import OAuthState

OAUTH_SECRET = "test-oauth-token-encryption-key"


class FakeMercadoLivreClient:
    def __init__(self, token_payload=None, refresh_payload=None, refresh_error=None):
        self.token_payload = token_payload or {
            "access_token": "access-token-123",
            "refresh_token": "refresh-token-123",
            "token_type": "bearer",
            "expires_in": 21600,
            "scope": "offline_access",
            "user_id": 123456,
        }
        self.refresh_payload = refresh_payload or {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "token_type": "bearer",
            "expires_in": 21600,
            "scope": "offline_access",
            "user_id": 123456,
        }
        self.refresh_error = refresh_error
        self.exchanged_code = None
        self.exchanged_verifier = None
        self.refresh_called = False

    def exchange_authorization_code(self, config, code, code_verifier):
        self.exchanged_code = code
        self.exchanged_verifier = code_verifier
        return self.token_payload

    def refresh_access_token(self, config, refresh_token):
        self.refresh_called = True
        if self.refresh_error:
            raise self.refresh_error
        self.refresh_token_used = refresh_token
        return self.refresh_payload


@pytest.fixture(autouse=True)
def mercadolivre_settings(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "mercadolivre_client_id", "ml-client-id")
    monkeypatch.setattr(settings, "mercadolivre_client_secret", "ml-client-secret")
    monkeypatch.setattr(
        settings,
        "mercadolivre_redirect_uri",
        "https://nature-dating-repeated.ngrok-free.dev/oauth/mercadolivre/callback",
    )
    monkeypatch.setattr(settings, "oauth_token_encryption_key", OAUTH_SECRET)


def auth_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "oauth@example.com", "full_name": "OAuth User", "password": "strong-password"},
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "oauth@example.com", "password": "strong-password"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def start_authorization(client):
    response = client.get("/api/v1/integrations/mercadolivre/authorize", headers=auth_headers(client))
    assert response.status_code == 200
    url = response.json()["authorization_url"]
    params = parse_qs(urlparse(url).query)
    return url, {key: values[0] for key, values in params.items()}


def get_user_id():
    with SessionLocal() as db:
        return db.query(OAuthState).first().user_id


def create_integration(user_id, access_token, refresh_token, expires_at, active=True):
    cipher = TokenCipher(OAUTH_SECRET)
    with SessionLocal() as db:
        integration = OAuthIntegration(
            user_id=user_id,
            provider=PROVIDER,
            provider_user_id="123456",
            access_token=cipher.encrypt(access_token),
            refresh_token=cipher.encrypt(refresh_token),
            token_type="bearer",
            expires_at=expires_at,
            scope="offline_access",
            is_active=active,
        )
        db.add(integration)
        db.commit()


def test_authorize_generates_mercadolivre_url_with_state_and_pkce(client):
    url, params = start_authorization(client)

    assert url.startswith(AUTHORIZATION_URL)
    assert params["response_type"] == "code"
    assert params["client_id"] == "ml-client-id"
    assert params["redirect_uri"] == "https://nature-dating-repeated.ngrok-free.dev/oauth/mercadolivre/callback"
    assert params["state"]
    assert params["code_challenge"]
    assert params["code_challenge_method"] == "S256"


def test_callback_validates_state_and_connects_without_returning_tokens(client, monkeypatch):
    _, params = start_authorization(client)
    fake_client = FakeMercadoLivreClient()
    monkeypatch.setattr("app.integrations.mercadolivre.service.MercadoLivreHttpClient", lambda: fake_client)

    response = client.get(f"/oauth/mercadolivre/callback?code=auth-code&state={params['state']}")

    assert response.status_code == 200
    assert response.json() == {"status": "connected", "provider": "mercadolivre"}
    assert "access_token" not in response.json()
    assert fake_client.exchanged_code == "auth-code"


def test_callback_rejects_invalid_state(client):
    response = client.get("/oauth/mercadolivre/callback?code=auth-code&state=invalid")

    assert response.status_code == 400


def test_pkce_verifier_is_encrypted_and_matches_authorization_challenge(client):
    _, params = start_authorization(client)

    with SessionLocal() as db:
        oauth_state = db.query(OAuthState).first()
        stored_verifier = oauth_state.code_verifier

    assert stored_verifier != params["code_challenge"]
    verifier = TokenCipher(OAUTH_SECRET).decrypt(stored_verifier)
    assert build_code_challenge(verifier) == params["code_challenge"]


def test_tokens_are_stored_encrypted_after_callback(client, monkeypatch):
    _, params = start_authorization(client)
    monkeypatch.setattr("app.integrations.mercadolivre.service.MercadoLivreHttpClient", lambda: FakeMercadoLivreClient())

    response = client.get(f"/oauth/mercadolivre/callback?code=auth-code&state={params['state']}")

    assert response.status_code == 200
    with SessionLocal() as db:
        integration = db.query(OAuthIntegration).first()
        assert integration.access_token != "access-token-123"
        assert integration.refresh_token != "refresh-token-123"
        assert TokenCipher(OAUTH_SECRET).decrypt(integration.access_token) == "access-token-123"


def test_status_returns_disconnected_when_user_has_no_tokens(client):
    response = client.get("/api/v1/integrations/mercadolivre/status", headers=auth_headers(client))

    assert response.status_code == 200
    assert response.json() == {
        "connected": False,
        "provider": "mercadolivre",
        "expires_at": None,
        "provider_user_id": None,
    }


def test_valid_access_token_is_reused_without_refresh(client):
    start_authorization(client)
    user_id = get_user_id()
    create_integration(user_id, "valid-access-token", "valid-refresh-token", now_utc() + timedelta(hours=1))
    fake_client = FakeMercadoLivreClient()

    with SessionLocal() as db:
        token = get_valid_access_token(db, user_id, fake_client)

    assert token == "valid-access-token"
    assert fake_client.refresh_called is False


def test_expired_access_token_is_refreshed_and_refresh_token_is_replaced(client):
    start_authorization(client)
    user_id = get_user_id()
    create_integration(user_id, "old-access-token", "old-refresh-token", now_utc() - timedelta(minutes=1))
    fake_client = FakeMercadoLivreClient()

    with SessionLocal() as db:
        token = get_valid_access_token(db, user_id, fake_client)

    assert token == "new-access-token"
    assert fake_client.refresh_called is True
    assert fake_client.refresh_token_used == "old-refresh-token"
    with SessionLocal() as db:
        integration = db.query(OAuthIntegration).first()
        assert TokenCipher(OAUTH_SECRET).decrypt(integration.refresh_token) == "new-refresh-token"


def test_refresh_failure_marks_integration_inactive(client):
    start_authorization(client)
    user_id = get_user_id()
    create_integration(user_id, "old-access-token", "old-refresh-token", now_utc() - timedelta(minutes=1))
    fake_client = FakeMercadoLivreClient(
        refresh_error=MercadoLivreAuthorizationRevokedError("Mercado Livre authorization is no longer valid")
    )

    with SessionLocal() as db:
        with pytest.raises(MercadoLivreAuthorizationRevokedError):
            get_valid_access_token(db, user_id, fake_client)

    with SessionLocal() as db:
        assert db.query(OAuthIntegration).first().is_active is False


def test_disconnect_removes_local_integration(client, monkeypatch):
    headers = auth_headers(client)
    response = client.get("/api/v1/integrations/mercadolivre/authorize", headers=headers)
    params = {key: values[0] for key, values in parse_qs(urlparse(response.json()["authorization_url"]).query).items()}
    monkeypatch.setattr("app.integrations.mercadolivre.service.MercadoLivreHttpClient", lambda: FakeMercadoLivreClient())
    client.get(f"/oauth/mercadolivre/callback?code=auth-code&state={params['state']}")

    delete_response = client.delete("/api/v1/integrations/mercadolivre", headers=headers)
    status_response = client.get("/api/v1/integrations/mercadolivre/status", headers=headers)

    assert delete_response.status_code == 204
    assert status_response.json()["connected"] is False
    with SessionLocal() as db:
        assert db.query(OAuthIntegration).count() == 0


def test_missing_configuration_returns_clear_error(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "mercadolivre_client_id", None)

    response = client.get("/api/v1/integrations/mercadolivre/authorize", headers=auth_headers(client))

    assert response.status_code == 503
    assert "MERCADOLIVRE_CLIENT_ID" in response.json()["detail"]


def test_oauth_flow_does_not_log_secrets(client, monkeypatch, caplog):
    _, params = start_authorization(client)
    monkeypatch.setattr("app.integrations.mercadolivre.service.MercadoLivreHttpClient", lambda: FakeMercadoLivreClient())

    response = client.get(f"/oauth/mercadolivre/callback?code=auth-code&state={params['state']}")

    assert response.status_code == 200
    assert "ml-client-secret" not in caplog.text
    assert "access-token-123" not in caplog.text
    assert "refresh-token-123" not in caplog.text
