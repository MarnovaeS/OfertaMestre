from functools import lru_cache

from app.core.config import settings
from app.integrations.awin.adapter import normalize_programs, normalize_promotions
from app.integrations.awin.client import AwinPublisherClient
from app.integrations.awin.exceptions import AwinConfigurationError
from app.integrations.awin.schemas import AwinProgramRead, AwinPromotionRead, AwinStatusResponse


def get_status() -> AwinStatusResponse:
    configured = _is_configured()
    return AwinStatusResponse(
        configured=configured,
        publisher_id=settings.awin_publisher_id.strip() if configured and settings.awin_publisher_id else None,
    )


def list_programs(*, country_code: str, relationship: str) -> list[AwinProgramRead]:
    payload = _build_client().get_programs(country_code=country_code.upper(), relationship=relationship)
    return normalize_programs(payload)


def list_promotions(
    *,
    page: int,
    page_size: int,
    membership: str,
    status: str,
    promotion_type: str,
    region_code: str,
    advertiser_id: int | None,
) -> list[AwinPromotionRead]:
    payload = _build_client().get_promotions(
        page=page,
        page_size=page_size,
        membership=membership,
        status=status,
        promotion_type=promotion_type,
        region_code=region_code.upper(),
        advertiser_id=advertiser_id,
    )
    return normalize_promotions(payload)


def _is_configured() -> bool:
    publisher_id = settings.awin_publisher_id.strip() if settings.awin_publisher_id else ""
    token = settings.awin_api_token.strip() if settings.awin_api_token else ""
    return bool(publisher_id.isdigit() and int(publisher_id) > 0 and token)


def _build_client() -> AwinPublisherClient:
    if not _is_configured():
        raise AwinConfigurationError("Awin publisher ID and API token are not configured correctly")
    return _shared_client(
        settings.awin_publisher_id.strip() if settings.awin_publisher_id else "",
        settings.awin_api_token.strip() if settings.awin_api_token else "",
        settings.awin_api_base_url,
    )


@lru_cache(maxsize=2)
def _shared_client(publisher_id: str, api_token: str, api_base_url: str) -> AwinPublisherClient:
    return AwinPublisherClient(
        publisher_id=publisher_id,
        api_token=api_token,
        api_base_url=api_base_url,
    )
