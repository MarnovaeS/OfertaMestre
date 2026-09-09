from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ExternalOfferInput(BaseModel):
    source: str = Field(min_length=1, max_length=100)
    external_id: str = Field(min_length=1, max_length=255)
    store_slug: str = Field(min_length=1, max_length=255)
    seller_external_id: str | None = Field(default=None, max_length=255)
    seller_name: str | None = Field(default=None, max_length=255)
    seller_is_official: bool | None = None
    title: str = Field(min_length=1, max_length=500)
    product_name: str = Field(min_length=1, max_length=255)
    brand_name: str | None = Field(default=None, max_length=255)
    category_name: str | None = Field(default=None, max_length=255)
    model: str | None = Field(default=None, max_length=255)
    gtin: str | None = Field(default=None, max_length=32)
    sku: str | None = Field(default=None, max_length=128)
    url: str = Field(min_length=1, max_length=2048)
    image_url: str | None = Field(default=None, max_length=2048)
    current_price: Decimal = Field(ge=0)
    original_price: Decimal | None = Field(default=None, ge=0)
    shipping_price: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="BRL", min_length=3, max_length=3)
    price_source: str | None = Field(default=None, min_length=1, max_length=100)
    price_source_class: str | None = Field(default=None, min_length=1, max_length=100)
    is_available: bool = True
    is_free_shipping: bool = False
    is_prime: bool | None = None
    installment_count: int | None = Field(default=None, ge=1)
    installment_value: Decimal | None = Field(default=None, ge=0)
    captured_at: datetime | None = None


class IngestionResult(BaseModel):
    product_id: int
    offer_id: int
    seller_id: int | None
    product_created: bool
    offer_created: bool
    seller_created: bool
    snapshot_created: bool
    matched_by: str
