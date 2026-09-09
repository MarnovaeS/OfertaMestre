from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.oauth_integration import OAuthIntegration
from app.models.store import Store
from app.models.user import User
from app.providers.registry import PROVIDERS, ProviderDefinition
from app.providers.schemas import ProviderIntegrationStatus, ProviderState


def list_provider_statuses(db: Session, user: User) -> list[ProviderIntegrationStatus]:
    stores = {row.slug for row in db.query(Store.slug).filter(Store.is_active.is_(True)).all()}
    ml_connected = (
        db.query(OAuthIntegration.id)
        .filter_by(user_id=user.id, provider="mercadolivre", is_active=True)
        .first()
        is not None
    )
    return [_status(definition, stores, ml_connected) for definition in PROVIDERS]


def _status(definition: ProviderDefinition, stores: set[str], ml_connected: bool) -> ProviderIntegrationStatus:
    configured = _configured(definition.provider)
    connected = definition.provider == "mercadolivre" and ml_connected
    state: ProviderState
    if connected:
        state = "connected"
    elif configured:
        state = "configured"
    elif definition.access_mode == "approval":
        state = "approval_required"
    elif definition.access_mode == "partnership":
        state = "partnership_required"
    else:
        state = "credentials_required"
    return ProviderIntegrationStatus(
        provider=definition.provider,
        name=definition.name,
        store_slug=definition.store_slug,
        channel=definition.channel,
        state=state,
        configured=configured,
        connected=connected,
        store_exists=None if definition.store_slug is None else definition.store_slug in stores,
        capabilities=list(definition.capabilities),
        note=definition.note,
        setup_url=definition.setup_url,
    )


def _configured(provider: str) -> bool:
    checks = {
        "mercadolivre": (settings.mercadolivre_client_id, settings.mercadolivre_client_secret, settings.mercadolivre_redirect_uri, settings.oauth_token_encryption_key),
        "steam": (settings.steam_web_api_key,),
        "amazon": (settings.amazon_creators_client_id, settings.amazon_creators_client_secret, settings.amazon_creators_partner_tag),
        "awin": (settings.awin_publisher_id, settings.awin_api_token),
        "magalu": (settings.magalu_client_id, settings.magalu_client_secret, settings.magalu_redirect_uri),
    }
    values = checks.get(provider)
    return bool(values and all(value and value.strip() for value in values))
