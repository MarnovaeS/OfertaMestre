from datetime import timedelta

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.integrations.mercadolivre import PROVIDER
from app.integrations.mercadolivre.client import MercadoLivreHttpClient
from app.integrations.mercadolivre.exceptions import (
    MercadoLivreAccessDeniedError,
    MercadoLivreAuthorizationRevokedError,
    MercadoLivreExpiredStateError,
    MercadoLivreInvalidStateError,
    MercadoLivreOAuthError,
    MercadoLivreReusedStateError,
)
from app.integrations.mercadolivre.oauth import (
    STATE_TTL_MINUTES,
    TOKEN_REFRESH_MARGIN,
    TokenCipher,
    as_utc,
    build_authorization_url,
    build_code_challenge,
    generate_code_verifier,
    generate_state,
    hash_state,
    now_utc,
    require_mercadolivre_settings,
)
from app.integrations.mercadolivre.schemas import (
    MercadoLivreAuthorizeResponse,
    MercadoLivreStatusResponse,
    MercadoLivreTokenResponse,
)
from app.models.oauth_integration import OAuthIntegration
from app.models.oauth_state import OAuthState
from app.models.user import User

CALLBACK_SUCCESS_MESSAGE = "Mercado Livre conectado com sucesso ao OfertaMestre."


def create_authorization(db: Session, user: User) -> MercadoLivreAuthorizeResponse:
    config = require_mercadolivre_settings()
    cipher = TokenCipher(config.token_encryption_key)
    state = generate_state()
    code_verifier = generate_code_verifier()
    code_challenge = build_code_challenge(code_verifier)

    oauth_state = OAuthState(
        user_id=user.id,
        provider=PROVIDER,
        state_hash=hash_state(state),
        code_verifier=cipher.encrypt(code_verifier),
        redirect_uri=config.redirect_uri,
        expires_at=now_utc() + timedelta(minutes=STATE_TTL_MINUTES),
    )
    db.add(oauth_state)
    db.commit()

    return MercadoLivreAuthorizeResponse(
        authorization_url=build_authorization_url(
            client_id=config.client_id,
            redirect_uri=config.redirect_uri,
            state=state,
            code_challenge=code_challenge,
        )
    )


def handle_callback(
    db: Session,
    code: str,
    state: str,
    http_client: MercadoLivreHttpClient | None = None,
) -> str:
    config = require_mercadolivre_settings()
    cipher = TokenCipher(config.token_encryption_key)
    oauth_state = _get_valid_state(db, state)
    code_verifier = cipher.decrypt(oauth_state.code_verifier)
    _consume_state(db, oauth_state)
    client = http_client or MercadoLivreHttpClient()

    try:
        token_payload = client.exchange_authorization_code(config, code, code_verifier)
        token_response = MercadoLivreTokenResponse.model_validate(token_payload)
        _upsert_integration(db, oauth_state.user_id, token_response, cipher)
        db.commit()
    except (MercadoLivreOAuthError, ValidationError):
        db.rollback()
        raise

    return CALLBACK_SUCCESS_MESSAGE


def handle_callback_denial(db: Session, state: str | None) -> None:
    if state:
        oauth_state = _get_valid_state(db, state)
        _consume_state(db, oauth_state)
    raise MercadoLivreAccessDeniedError("Mercado Livre authorization was denied by the user")


def get_status(db: Session, user: User) -> MercadoLivreStatusResponse:
    integration = _get_integration(db, user.id)
    if integration is None or not integration.is_active:
        return MercadoLivreStatusResponse(connected=False)
    return MercadoLivreStatusResponse(
        connected=True,
        expires_at=integration.expires_at,
        provider_user_id=integration.provider_user_id,
    )


def disconnect(db: Session, user: User) -> None:
    integration = _get_integration(db, user.id)
    if integration is None:
        return
    db.delete(integration)
    db.commit()


def get_valid_access_token(
    db: Session,
    user_id: int,
    http_client: MercadoLivreHttpClient | None = None,
) -> str:
    config = require_mercadolivre_settings()
    cipher = TokenCipher(config.token_encryption_key)
    integration = _get_integration(db, user_id)
    if integration is None or not integration.is_active:
        raise MercadoLivreAuthorizationRevokedError("Mercado Livre integration is not connected")

    if as_utc(integration.expires_at) > now_utc() + TOKEN_REFRESH_MARGIN:
        return cipher.decrypt(integration.access_token)

    client = http_client or MercadoLivreHttpClient()
    try:
        token_payload = client.refresh_access_token(config, cipher.decrypt(integration.refresh_token))
        token_response = MercadoLivreTokenResponse.model_validate(token_payload)
    except (MercadoLivreAuthorizationRevokedError, ValidationError):
        integration.is_active = False
        db.commit()
        raise
    except MercadoLivreOAuthError:
        db.rollback()
        raise

    _apply_token_response(integration, token_response, cipher)
    db.commit()
    return cipher.decrypt(integration.access_token)


def _get_valid_state(db: Session, state: str) -> OAuthState:
    oauth_state = db.query(OAuthState).filter(OAuthState.provider == PROVIDER, OAuthState.state_hash == hash_state(state)).first()
    if oauth_state is None:
        raise MercadoLivreInvalidStateError("Invalid Mercado Livre OAuth state")
    if oauth_state.consumed:
        raise MercadoLivreReusedStateError("Mercado Livre OAuth state was already used")
    if as_utc(oauth_state.expires_at) <= now_utc():
        raise MercadoLivreExpiredStateError("Mercado Livre OAuth state is expired")
    return oauth_state


def _consume_state(db: Session, oauth_state: OAuthState) -> None:
    oauth_state.consumed = True
    db.commit()
    db.refresh(oauth_state)


def _get_integration(db: Session, user_id: int) -> OAuthIntegration | None:
    return db.query(OAuthIntegration).filter(OAuthIntegration.user_id == user_id, OAuthIntegration.provider == PROVIDER).first()


def _upsert_integration(
    db: Session,
    user_id: int,
    token_response: MercadoLivreTokenResponse,
    cipher: TokenCipher,
) -> OAuthIntegration:
    integration = _get_integration(db, user_id)
    if integration is None:
        integration = OAuthIntegration(
            user_id=user_id,
            provider=PROVIDER,
            access_token="",
            refresh_token="",
            token_type=token_response.token_type,
            expires_at=now_utc(),
        )
        db.add(integration)
    _apply_token_response(integration, token_response, cipher)
    return integration


def _apply_token_response(
    integration: OAuthIntegration,
    token_response: MercadoLivreTokenResponse,
    cipher: TokenCipher,
) -> None:
    if not token_response.refresh_token and not integration.refresh_token:
        raise MercadoLivreOAuthError("Mercado Livre OAuth response did not include a refresh token")

    integration.access_token = cipher.encrypt(token_response.access_token)
    if token_response.refresh_token:
        integration.refresh_token = cipher.encrypt(token_response.refresh_token)
    integration.token_type = token_response.token_type
    integration.expires_at = now_utc() + timedelta(seconds=token_response.expires_in)
    integration.scope = token_response.scope
    integration.provider_user_id = str(token_response.user_id) if token_response.user_id is not None else integration.provider_user_id
    integration.is_active = True
