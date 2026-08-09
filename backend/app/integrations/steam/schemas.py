from pydantic import BaseModel, Field


class SteamStatusResponse(BaseModel):
    configured: bool
    provider: str = "steam"
    store_exists: bool


class SteamAppRead(BaseModel):
    appid: int
    name: str
    last_modified: int | None = None
    price_change_number: int | None = None


class SteamSyncResult(BaseModel):
    provider: str = "steam"
    catalog_items_seen: int
    catalog_items_created: int
    catalog_items_updated: int
    changed_appids: list[int] = Field(default_factory=list)
    cursor: str | None = None
    last_modified: int | None = None
    price_data_available: bool = False
    offers_ingested: int = 0
    price_snapshots_created: int = 0


class SteamPriceRead(BaseModel):
    provider: str = "steam"
    appid: int
    currency: str
    original_price: str | None = None
    current_price: str
    discount_percent: int
    price_source: str = "store_appdetails"
    price_source_class: str = "undocumented_public"
    is_free: bool = False
