from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.ingestion.contracts import ExternalOfferInput

STORE_SLUG = "mercadolivre"
SOURCE = "mercadolivre"

BRAND_ATTRIBUTE_IDS = {"BRAND", "MARCA"}
MODEL_ATTRIBUTE_IDS = {"MODEL", "MODELO"}
GTIN_ATTRIBUTE_IDS = {"GTIN", "EAN", "UPC", "JAN", "ISBN"}
SKU_ATTRIBUTE_IDS = {"SELLER_SKU", "SKU"}


def normalize_item(
    item: dict[str, Any],
    *,
    sale_price: dict[str, Any] | None = None,
    seller: dict[str, Any] | None = None,
    captured_at: datetime | None = None,
) -> ExternalOfferInput:
    attributes = item.get("attributes") if isinstance(item.get("attributes"), list) else []
    current_price, original_price, currency = _extract_prices(item, sale_price)
    shipping = item.get("shipping") if isinstance(item.get("shipping"), dict) else {}
    pictures = item.get("pictures") if isinstance(item.get("pictures"), list) else []
    installments = item.get("installments") if isinstance(item.get("installments"), dict) else {}

    seller_id = item.get("seller_id")
    seller_name = _seller_name(seller)

    return ExternalOfferInput(
        source=SOURCE,
        external_id=str(item.get("id")),
        store_slug=STORE_SLUG,
        seller_external_id=str(seller_id) if seller_id is not None else None,
        seller_name=seller_name,
        seller_is_official=item.get("official_store_id") is not None,
        title=str(item.get("title")),
        product_name=str(item.get("title")),
        brand_name=_attribute_value(attributes, BRAND_ATTRIBUTE_IDS),
        category_name=None,
        model=_attribute_value(attributes, MODEL_ATTRIBUTE_IDS),
        gtin=_attribute_value(attributes, GTIN_ATTRIBUTE_IDS),
        sku=_attribute_value(attributes, SKU_ATTRIBUTE_IDS),
        url=str(item.get("permalink")),
        image_url=_image_url(item, pictures),
        current_price=current_price,
        original_price=original_price,
        shipping_price=Decimal("0.00") if shipping.get("free_shipping") is True else None,
        currency=currency,
        is_available=_is_available(item),
        is_free_shipping=bool(shipping.get("free_shipping")),
        is_prime=None,
        installment_count=_optional_int(installments.get("quantity")),
        installment_value=_optional_decimal(installments.get("amount")),
        captured_at=captured_at or datetime.now(UTC),
    )


def _extract_prices(item: dict[str, Any], sale_price: dict[str, Any] | None) -> tuple[Decimal, Decimal | None, str]:
    if sale_price and sale_price.get("amount") is not None:
        return (
            _decimal(sale_price.get("amount")),
            _optional_decimal(sale_price.get("regular_amount")),
            str(sale_price.get("currency_id") or item.get("currency_id") or "BRL"),
        )

    return (
        _decimal(item.get("price")),
        _optional_decimal(item.get("original_price")),
        str(item.get("currency_id") or "BRL"),
    )


def _attribute_value(attributes: list[dict[str, Any]], ids: set[str]) -> str | None:
    for attribute in attributes:
        attribute_id = str(attribute.get("id") or attribute.get("name") or "").upper()
        if attribute_id in ids and attribute.get("value_name"):
            return str(attribute["value_name"])
    return None


def _image_url(item: dict[str, Any], pictures: list[dict[str, Any]]) -> str | None:
    thumbnail = item.get("secure_thumbnail") or item.get("thumbnail")
    if thumbnail:
        return str(thumbnail)
    if pictures:
        first = pictures[0]
        if isinstance(first, dict) and first.get("secure_url"):
            return str(first["secure_url"])
        if isinstance(first, dict) and first.get("url"):
            return str(first["url"])
    return None


def _seller_name(seller: dict[str, Any] | None) -> str | None:
    if not seller:
        return None
    nickname = seller.get("nickname")
    return str(nickname) if nickname else None


def _is_available(item: dict[str, Any]) -> bool:
    status = item.get("status")
    quantity = item.get("available_quantity")
    if status is not None and status != "active":
        return False
    return quantity is None or int(quantity) > 0


def _decimal(value: Any) -> Decimal:
    if value is None:
        raise ValueError("Mercado Livre item price is missing")
    return Decimal(str(value))


def _optional_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
