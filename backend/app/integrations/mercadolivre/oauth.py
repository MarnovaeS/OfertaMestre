from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import base64
import hashlib
import secrets
from urllib.parse import urlencode

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.integrations.mercadolivre import AUTHORIZATION_URL
from app.integrations.mercadolivre.exceptions import MercadoLivreConfigurationError, MercadoLivreOAuthError

STATE_TTL_MINUTES = 10
TOKEN_REFRESH_MARGIN = timedelta(minutes=5)


@dataclass(frozen=True)
class MercadoLivreOAuthSettings:
    client_id: str
    client_secret: str
    redirect_uri: str
    token_encryption_key: str


def now_utc() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def require_mercadolivre_settings() -> MercadoLivreOAuthSettings:
    missing = [
        name
        for name, value in {
            "MERCADOLIVRE_CLIENT_ID": settings.mercadolivre_client_id,
            "MERCADOLIVRE_CLIENT_SECRET": settings.mercadolivre_client_secret,
            "MERCADOLIVRE_REDIRECT_URI": settings.mercadolivre_redirect_uri,
            "OAUTH_TOKEN_ENCRYPTION_KEY": settings.oauth_token_encryption_key,
        }.items()
        if not value
    ]
    if missing:
        raise MercadoLivreConfigurationError(f"Mercado Livre OAuth is not configured: {', '.join(missing)}")

    return MercadoLivreOAuthSettings(
        client_id=str(settings.mercadolivre_client_id),
        client_secret=str(settings.mercadolivre_client_secret),
        redirect_uri=str(settings.mercadolivre_redirect_uri),
        token_encryption_key=str(settings.oauth_token_encryption_key),
    )


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def hash_state(state: str) -> str:
    return hashlib.sha256(state.encode("utf-8")).hexdigest()


def generate_code_verifier() -> str:
    return secrets.token_urlsafe(64)


def build_code_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def build_authorization_url(client_id: str, redirect_uri: str, state: str, code_challenge: str) -> str:
    query = urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"{AUTHORIZATION_URL}?{query}"


class TokenCipher:
    def __init__(self, secret: str) -> None:
        key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
        self._fernet = Fernet(key)

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise MercadoLivreOAuthError("Stored Mercado Livre token could not be decrypted") from exc
