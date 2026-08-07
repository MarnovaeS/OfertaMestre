from datetime import datetime

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    brand_id: int | None = None
    category_id: int | None = None
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    model: str | None = Field(default=None, max_length=255)
    description: str | None = None
    gtin: str | None = Field(default=None, max_length=32)
    sku: str | None = Field(default=None, max_length=128)
    image_url: str | None = Field(default=None, max_length=2048)
    is_active: bool = True


class ProductUpdate(BaseModel):
    brand_id: int | None = None
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    model: str | None = Field(default=None, max_length=255)
    description: str | None = None
    gtin: str | None = Field(default=None, max_length=32)
    sku: str | None = Field(default=None, max_length=128)
    image_url: str | None = Field(default=None, max_length=2048)
    is_active: bool | None = None


class ProductRead(BaseModel):
    id: int
    brand_id: int | None
    category_id: int | None
    name: str
    slug: str
    model: str | None
    description: str | None
    gtin: str | None
    sku: str | None
    image_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
