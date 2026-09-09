from decimal import Decimal, InvalidOperation

from app.integrations.amazon.schemas import AmazonItemRead


def normalize_search_response(payload: dict) -> list[AmazonItemRead]:
    result = payload.get("searchResult", payload.get("searchItemsResult", {}))
    items = result.get("items", []) if isinstance(result, dict) else []
    return [normalized for item in items if isinstance(item, dict) and (normalized := _normalize_item(item))]


def _normalize_item(item: dict) -> AmazonItemRead | None:
    asin = _text(item.get("asin"))
    title = _text(_path(item, "itemInfo", "title", "displayValue"))
    url = _text(item.get("detailPageURL"))
    if not asin or not title or not url:
        return None
    listing = _first(_path(item, "offersV2", "listings"))
    price = _money(_path(listing, "price", "money"))
    original = _money(_path(listing, "price", "savingBasis", "money"))
    if original is None:
        original = _money(_path(listing, "savingBasis", "money"))
    currency = _text(_path(listing, "price", "money", "currency"))
    seller_name = _text(_path(listing, "merchantInfo", "name"))
    seller_id = _text(_path(listing, "merchantInfo", "id"))
    availability = _text(_path(listing, "availability", "type"))
    discount = None
    if price is not None and original and original > 0 and price <= original:
        discount = int(round((original - price) * 100 / original))
    return AmazonItemRead(
        asin=asin,
        title=title,
        url=url,
        image_url=_text(_path(item, "images", "primary", "medium", "url")),
        current_price=price,
        original_price=original,
        currency=currency,
        discount_percent=discount,
        seller_name=seller_name,
        seller_external_id=seller_id,
        is_available=None if not availability else availability.lower() not in {"outofstock", "unavailable"},
    )


def _path(value, *keys):
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _first(value):
    return value[0] if isinstance(value, list) and value and isinstance(value[0], dict) else {}


def _text(value) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _money(value) -> Decimal | None:
    amount = value.get("amount") if isinstance(value, dict) else None
    try:
        result = Decimal(str(amount))
    except (InvalidOperation, TypeError):
        return None
    return result if result >= 0 else None
