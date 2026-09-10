from typing import Literal

from pydantic import BaseModel


class AwinStatusResponse(BaseModel):
    provider: str = "awin"
    configured: bool
    publisher_id: str | None = None


class AwinRegionRead(BaseModel):
    name: str | None = None
    country_code: str | None = None


class AwinProgramRead(BaseModel):
    advertiser_id: int
    name: str
    status: str | None = None
    currency: str | None = None
    display_url: str | None = None
    tracking_url: str | None = None
    logo_url: str | None = None
    primary_region: AwinRegionRead | None = None


class AwinAdvertiserRead(BaseModel):
    id: int
    name: str
    joined: bool | None = None


class AwinPromotionRead(BaseModel):
    promotion_id: int
    type: Literal["promotion", "voucher"] | str
    title: str
    description: str | None = None
    terms: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    url: str | None = None
    tracking_url: str | None = None
    advertiser: AwinAdvertiserRead | None = None
    voucher_code: str | None = None
