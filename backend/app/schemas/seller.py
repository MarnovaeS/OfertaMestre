from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SellerCreate(BaseModel):
    store_id: int
    name: str = Field(min_length=1, max_length=255)
    external_id: str | None = Field(default=None, max_length=255)
    reputation_score: Decimal | None = Field(default=None, ge=0)
    is_official: bool = False


class SellerUpdate(BaseModel):
    store_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    external_id: str | None = Field(default=None, max_length=255)
    reputation_score: Decimal | None = Field(default=None, ge=0)
    is_official: bool | None = None


class SellerRead(BaseModel):
    id: int
    store_id: int
    name: str
    external_id: str | None
    reputation_score: Decimal | None
    is_official: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
