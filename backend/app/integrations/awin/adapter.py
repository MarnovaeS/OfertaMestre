from app.integrations.awin.schemas import (
    AwinAdvertiserRead,
    AwinProgramRead,
    AwinPromotionRead,
    AwinRegionRead,
)


def normalize_programs(payload: object) -> list[AwinProgramRead]:
    rows = payload if isinstance(payload, list) else []
    return [normalized for row in rows if isinstance(row, dict) and (normalized := _normalize_program(row))]


def normalize_promotions(payload: object) -> list[AwinPromotionRead]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        candidate = payload.get("data", payload.get("promotions", []))
        rows = candidate if isinstance(candidate, list) else []
    else:
        rows = []
    return [normalized for row in rows if isinstance(row, dict) and (normalized := _normalize_promotion(row))]


def _normalize_program(row: dict) -> AwinProgramRead | None:
    advertiser_id = _integer(row.get("id"))
    name = _text(row.get("name"))
    if advertiser_id is None or not name:
        return None
    region = row.get("primaryRegion")
    normalized_region = None
    if isinstance(region, dict):
        normalized_region = AwinRegionRead(
            name=_text(region.get("name")),
            country_code=_text(region.get("countryCode")),
        )
    return AwinProgramRead(
        advertiser_id=advertiser_id,
        name=name,
        status=_text(row.get("status")),
        currency=_text(row.get("currencyCode")),
        display_url=_text(row.get("displayUrl")),
        tracking_url=_text(row.get("clickThroughUrl")),
        logo_url=_text(row.get("logoUrl")),
        primary_region=normalized_region,
    )


def _normalize_promotion(row: dict) -> AwinPromotionRead | None:
    promotion_id = _integer(row.get("promotionId"))
    title = _text(row.get("title"))
    promotion_type = _text(row.get("type"))
    if promotion_id is None or not title or not promotion_type:
        return None
    advertiser = row.get("advertiser")
    normalized_advertiser = None
    if isinstance(advertiser, dict):
        advertiser_id = _integer(advertiser.get("id"))
        advertiser_name = _text(advertiser.get("name"))
        if advertiser_id is not None and advertiser_name:
            joined = advertiser.get("joined")
            normalized_advertiser = AwinAdvertiserRead(
                id=advertiser_id,
                name=advertiser_name,
                joined=joined if isinstance(joined, bool) else None,
            )
    voucher = row.get("voucher")
    return AwinPromotionRead(
        promotion_id=promotion_id,
        type=promotion_type,
        title=title,
        description=_text(row.get("description")),
        terms=_text(row.get("terms")),
        start_date=_text(row.get("startDate")),
        end_date=_text(row.get("endDate")),
        url=_text(row.get("url")),
        tracking_url=_text(row.get("urlTracking")),
        advertiser=normalized_advertiser,
        voucher_code=_text(voucher.get("code")) if isinstance(voucher, dict) else None,
    )


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _integer(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if not isinstance(value, str) or not value.strip().isdigit():
        return None
    result = int(value.strip())
    return result if result > 0 else None
