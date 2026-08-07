from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ProductOfferCreate(BaseModel):
    product_id: int
    store_id: int
    seller_id: int | None = None
    external_id: str = Field(min_length=1, max_length=255)
    url: str = Field(min_length=1, max_length=2048)
    title: str = Field(min_length=1, max_length=500)
    current_price: Decimal = Field(ge=0)
    original_price: Decimal | None = Field(default=None, ge=0)
    shipping_price: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="BRL", min_length=3, max_length=3)
    is_available: bool = True
    is_prime: bool | None = None
    is_free_shipping: bool = False
    installment_count: int | None = Field(default=None, ge=1)
    installment_value: Decimal | None = Field(default=None, ge=0)
    last_checked_at: datetime | None = None


class ProductOfferUpdate(BaseModel):
    product_id: int | None = None
    store_id: int | None = None
    seller_id: int | None = None
    external_id: str | None = Field(default=None, min_length=1, max_length=255)
    url: str | None = Field(default=None, min_length=1, max_length=2048)
    title: str | None = Field(default=None, min_length=1, max_length=500)
    current_price: Decimal | None = Field(default=None, ge=0)
    original_price: Decimal | None = Field(default=None, ge=0)
    shipping_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    is_available: bool | None = None
    is_prime: bool | None = None
    is_free_shipping: bool | None = None
    installment_count: int | None = Field(default=None, ge=1)
    installment_value: Decimal | None = Field(default=None, ge=0)
    last_checked_at: datetime | None = None


class ProductOfferRead(BaseModel):
    id: int
    product_id: int
    store_id: int
    seller_id: int | None
    external_id: str
    url: str
    title: str
    current_price: Decimal
    original_price: Decimal | None
    shipping_price: Decimal | None
    currency: str
    is_available: bool
    is_prime: bool | None
    is_free_shipping: bool
    installment_count: int | None
    installment_value: Decimal | None
    last_checked_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
