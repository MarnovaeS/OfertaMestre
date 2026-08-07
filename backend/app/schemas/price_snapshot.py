from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PriceSnapshotCreate(BaseModel):
    price: Decimal = Field(ge=0)
    original_price: Decimal | None = Field(default=None, ge=0)
    shipping_price: Decimal | None = Field(default=None, ge=0)
    captured_at: datetime | None = None


class PriceSnapshotRead(BaseModel):
    id: int
    product_offer_id: int
    price: Decimal
    original_price: Decimal | None
    shipping_price: Decimal | None
    captured_at: datetime

    model_config = {"from_attributes": True}
