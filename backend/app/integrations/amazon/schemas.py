from decimal import Decimal

from pydantic import BaseModel


class AmazonStatusResponse(BaseModel):
    provider: str = "amazon"
    configured: bool
    store_exists: bool
    marketplace: str


class AmazonItemRead(BaseModel):
    asin: str
    title: str
    url: str
    image_url: str | None = None
    current_price: Decimal | None = None
    original_price: Decimal | None = None
    currency: str | None = None
    discount_percent: int | None = None
    seller_name: str | None = None
    seller_external_id: str | None = None
    is_available: bool | None = None
