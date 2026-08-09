from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PriceSnapshotCreate(BaseModel):
    price: Decimal = Field(ge=0)
    original_price: Decimal | None = Field(default=None, ge=0)
    shipping_price: Decimal | None = Field(default=None, ge=0)
    price_source: str | None = Field(default=None, min_length=1, max_length=100)
    price_source_class: str | None = Field(default=None, min_length=1, max_length=100)
    captured_at: datetime | None = None


class PriceSnapshotRead(BaseModel):
    id: int
    product_offer_id: int
    price: Decimal
    original_price: Decimal | None
    shipping_price: Decimal | None
    price_source: str | None
    price_source_class: str | None
    captured_at: datetime

    model_config = {"from_attributes": True}
