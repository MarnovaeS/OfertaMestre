from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.exceptions.domain import DomainNotFoundError
from app.ingestion.contracts import ExternalOfferInput
from app.ingestion.service import ingest_external_offer
from app.integrations.steam import PROVIDER, STORE_SLUG
from app.integrations.steam.client import SteamStoreClient
from app.integrations.steam.exceptions import SteamConfigurationError, SteamPriceDisabledError
from app.integrations.steam.price_client import SteamPrice, SteamStorePriceClient
from app.integrations.steam.schemas import SteamAppRead, SteamIngestResult, SteamPriceRead, SteamStatusResponse, SteamSyncResult
from app.models.provider_catalog_item import ProviderCatalogItem
from app.models.provider_sync_state import ProviderSyncState
from app.models.store import Store
from app.providers.change_detection import has_app_changed
from app.providers.contracts import CatalogItem


def get_status(db: Session) -> SteamStatusResponse:
    return SteamStatusResponse(configured=bool(settings.steam_web_api_key), store_exists=_store_exists(db))


def list_apps(
    *,
    max_results: int,
    last_appid: int | None = None,
    modified_since: int | None = None,
    include_games: bool = True,
    include_dlc: bool = False,
    client: SteamStoreClient | None = None,
) -> list[SteamAppRead]:
    steam_client = client or _build_client()
    payload = steam_client.get_app_list(
        max_results=max_results,
        last_appid=last_appid,
        if_modified_since=modified_since,
        include_games=include_games,
        include_dlc=include_dlc,
    )
    return [_to_app_read(item) for item in _response_apps(payload)]


def get_app_price(appid: int, *, client: SteamStorePriceClient | None = None) -> SteamPriceRead:
    price = _get_price(appid, client=client)
    return _price_read(price)


def ingest_app_offer(
    db: Session,
    appid: int,
    *,
    client: SteamStorePriceClient | None = None,
) -> SteamIngestResult:
    _require_store(db)
    catalog_item = db.scalars(
        select(ProviderCatalogItem).where(
            ProviderCatalogItem.provider == PROVIDER,
            ProviderCatalogItem.external_id == str(appid),
        )
    ).first()
    if catalog_item is None:
        raise DomainNotFoundError("Steam catalog item not found")

    price = _get_price(appid, client=client)
    metadata = dict(catalog_item.metadata_json or {})
    metadata.update(
        {
            "price_data_available": True,
            "price_source": price.price_source,
            "price_source_class": price.price_source_class,
            "currency": price.currency,
            "discount_percent": price.discount_percent,
            "is_free": price.is_free,
        }
    )
    catalog_item.metadata_json = metadata
    db.flush()

    if price.is_free:
        db.commit()
        return SteamIngestResult(appid=appid, catalog_only=True, is_free=True)

    payload = ExternalOfferInput(
        source=PROVIDER,
        external_id=str(appid),
        store_slug=STORE_SLUG,
        title=catalog_item.name,
        product_name=catalog_item.name,
        url=f"{settings.steam_store_base_url.rstrip('/')}/app/{appid}",
        current_price=price.current_price,
        original_price=price.original_price,
        shipping_price=None,
        currency=price.currency,
        price_source=price.price_source,
        price_source_class=price.price_source_class,
        is_available=True,
        is_free_shipping=False,
    )
    result = ingest_external_offer(db, payload)
    return SteamIngestResult(appid=appid, **result.model_dump())


def sync_catalog(
    db: Session,
    *,
    max_results: int,
    last_appid: int | None = None,
    modified_since: int | None = None,
    include_games: bool = True,
    include_dlc: bool = False,
    client: SteamStoreClient | None = None,
) -> SteamSyncResult:
    store = _require_store(db)
    apps = list_apps(
        max_results=max_results,
        last_appid=last_appid,
        modified_since=modified_since,
        include_games=include_games,
        include_dlc=include_dlc,
        client=client,
    )
    created = 0
    updated = 0
    changed_appids: list[int] = []
    max_appid = last_appid
    max_last_modified = modified_since

    for app in apps:
        current = CatalogItem(
            provider=PROVIDER,
            external_id=str(app.appid),
            name=app.name,
            last_modified=app.last_modified,
            price_change_number=app.price_change_number,
        )
        row = db.scalars(
            select(ProviderCatalogItem).where(
                ProviderCatalogItem.provider == PROVIDER,
                ProviderCatalogItem.external_id == str(app.appid),
            )
        ).first()
        previous = _catalog_item_from_row(row) if row else None
        changed = has_app_changed(previous, current)

        if row is None:
            row = ProviderCatalogItem(
                provider=PROVIDER,
                store_id=store.id,
                external_id=str(app.appid),
                name=app.name,
                last_modified=app.last_modified,
                price_change_number=app.price_change_number,
                metadata_json={"price_data_available": False},
            )
            db.add(row)
            created += 1
        elif changed:
            row.store_id = store.id
            row.name = app.name
            row.last_modified = app.last_modified
            row.price_change_number = app.price_change_number
            row.metadata_json = {"price_data_available": False}
            row.last_seen_at = datetime.now(UTC)
            updated += 1
        else:
            row.last_seen_at = datetime.now(UTC)

        if changed:
            changed_appids.append(app.appid)
        max_appid = max(max_appid or app.appid, app.appid)
        if app.last_modified is not None:
            max_last_modified = max(max_last_modified or app.last_modified, app.last_modified)

    state = _get_or_create_state(db)
    state.cursor = str(max_appid) if max_appid is not None else state.cursor
    state.last_sync_at = datetime.now(UTC)
    state.metadata_json = {"last_appid": max_appid, "last_modified": max_last_modified}
    db.commit()

    return SteamSyncResult(
        catalog_items_seen=len(apps),
        catalog_items_created=created,
        catalog_items_updated=updated,
        changed_appids=changed_appids,
        cursor=state.cursor,
        last_modified=max_last_modified,
    )


@lru_cache(maxsize=4)
def _shared_price_client(base_url: str) -> SteamStorePriceClient:
    return SteamStorePriceClient(base_url=base_url)


def _build_price_client() -> SteamStorePriceClient:
    if not settings.steam_appdetails_enabled:
        raise SteamPriceDisabledError("Steam appdetails price enrichment is disabled")
    return _shared_price_client(settings.steam_store_base_url)


def _get_price(appid: int, *, client: SteamStorePriceClient | None = None) -> SteamPrice:
    if not settings.steam_appdetails_enabled:
        raise SteamPriceDisabledError("Steam appdetails price enrichment is disabled")
    price_client = client or _build_price_client()
    return price_client.get_price(appid, country_code=settings.steam_country_code)


def _price_read(price: SteamPrice) -> SteamPriceRead:
    return SteamPriceRead(
        appid=price.appid,
        currency=price.currency,
        original_price=str(price.original_price) if price.original_price is not None else None,
        current_price=str(price.current_price),
        discount_percent=price.discount_percent,
        price_source=price.price_source,
        price_source_class=price.price_source_class,
        is_free=price.is_free,
    )


def _build_client() -> SteamStoreClient:
    if not settings.steam_web_api_key:
        raise SteamConfigurationError("STEAM_WEB_API_KEY is not configured")
    return SteamStoreClient(settings.steam_web_api_key, base_url=settings.steam_web_api_base_url)


def _store_exists(db: Session) -> bool:
    return db.scalars(select(Store.id).where(Store.slug == STORE_SLUG)).first() is not None


def _require_store(db: Session) -> Store:
    store = db.scalars(select(Store).where(Store.slug == STORE_SLUG)).first()
    if store is None:
        raise DomainNotFoundError("Store steam not found")
    return store


def _get_or_create_state(db: Session) -> ProviderSyncState:
    state = db.scalars(select(ProviderSyncState).where(ProviderSyncState.provider == PROVIDER)).first()
    if state is None:
        state = ProviderSyncState(provider=PROVIDER)
        db.add(state)
        db.flush()
    return state


def _response_apps(payload: dict[str, Any]) -> list[dict[str, Any]]:
    response = payload.get("response") if isinstance(payload.get("response"), dict) else payload
    apps = response.get("apps") if isinstance(response, dict) else []
    return apps if isinstance(apps, list) else []


def _to_app_read(item: dict[str, Any]) -> SteamAppRead:
    return SteamAppRead(
        appid=int(item["appid"]),
        name=str(item["name"]).strip(),
        last_modified=_optional_int(item.get("last_modified")),
        price_change_number=_optional_int(item.get("price_change_number")),
    )


def _catalog_item_from_row(row: ProviderCatalogItem) -> CatalogItem:
    return CatalogItem(
        provider=row.provider,
        external_id=row.external_id,
        name=row.name,
        last_modified=row.last_modified,
        price_change_number=row.price_change_number,
        metadata=row.metadata_json,
    )


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
