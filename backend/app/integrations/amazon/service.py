from functools import lru_cache

from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.amazon.adapter import normalize_search_response
from app.integrations.amazon.client import AmazonCreatorsClient
from app.integrations.amazon.exceptions import AmazonConfigurationError
from app.integrations.amazon.schemas import AmazonItemRead, AmazonStatusResponse
from app.models.store import Store


def get_status(db: Session) -> AmazonStatusResponse:
    return AmazonStatusResponse(
        configured=_is_configured(),
        store_exists=db.query(Store.id).filter_by(slug="amazon-brasil", is_active=True).first() is not None,
        marketplace=settings.amazon_creators_marketplace,
    )


def search_items(keywords: str, *, item_count: int = 10) -> list[AmazonItemRead]:
    client = _build_client()
    return normalize_search_response(client.search_items(keywords, item_count=item_count))


def _is_configured() -> bool:
    return all(
        value and value.strip()
        for value in (
            settings.amazon_creators_client_id,
            settings.amazon_creators_client_secret,
            settings.amazon_creators_partner_tag,
        )
    )


def _build_client() -> AmazonCreatorsClient:
    if not _is_configured():
        raise AmazonConfigurationError("Amazon Creators API credentials are not configured")
    return _shared_client(
        settings.amazon_creators_client_id or "",
        settings.amazon_creators_client_secret or "",
        settings.amazon_creators_partner_tag or "",
        settings.amazon_creators_marketplace,
        settings.amazon_creators_api_base_url,
        settings.amazon_creators_token_url,
    )


@lru_cache(maxsize=2)
def _shared_client(
    client_id: str,
    client_secret: str,
    partner_tag: str,
    marketplace: str,
    api_base_url: str,
    token_url: str,
) -> AmazonCreatorsClient:
    return AmazonCreatorsClient(
        client_id=client_id,
        client_secret=client_secret,
        partner_tag=partner_tag,
        marketplace=marketplace,
        api_base_url=api_base_url,
        token_url=token_url,
    )
