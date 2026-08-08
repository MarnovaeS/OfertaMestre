from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.ingestion.contracts import ExternalOfferInput
from app.integrations.mercadolivre.exceptions import MercadoLivreNormalizationError

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
    external_id = _required_str(item, "id")
    title = _required_str(item, "title")
    url = _required_str(item, "permalink")
    current_price, original_price, currency = _extract_prices(item, sale_price)

    attributes = item.get("attributes") if isinstance(item.get("attributes"), list) else []
    shipping = item.get("shipping") if isinstance(item.get("shipping"), dict) else {}
    pictures = item.get("pictures") if isinstance(item.get("pictures"), list) else []
    installments = item.get("installments") if isinstance(item.get("installments"), dict) else {}

    return ExternalOfferInput(
        source=SOURCE,
        external_id=external_id,
        store_slug=STORE_SLUG,
        seller_external_id=_optional_str(item.get("seller_id")),
        seller_name=_seller_name(seller),
        seller_is_official=item.get("official_store_id") is not None,
        title=title,
        product_name=title,
        brand_name=_attribute_value(attributes, BRAND_ATTRIBUTE_IDS),
        category_name=None,
        model=_attribute_value(attributes, MODEL_ATTRIBUTE_IDS),
        gtin=_attribute_value(attributes, GTIN_ATTRIBUTE_IDS),
        sku=_attribute_value(attributes, SKU_ATTRIBUTE_IDS),
        url=url,
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
    if sale_price and _has_value(sale_price.get("amount")):
        return (
            _required_decimal(sale_price.get("amount"), "sale_price.amount"),
            _optional_decimal(sale_price.get("regular_amount"), "sale_price.regular_amount"),
            _required_currency(sale_price.get("currency_id") or item.get("currency_id")),
        )

    return (
        _required_decimal(item.get("price"), "price"),
        _optional_decimal(item.get("original_price"), "original_price"),
        _required_currency(item.get("currency_id")),
    )


def _attribute_value(attributes: list[dict[str, Any]], ids: set[str]) -> str | None:
    for attribute in attributes:
        attribute_id = str(attribute.get("id") or attribute.get("name") or "").upper()
        value = _optional_str(attribute.get("value_name"))
        if attribute_id in ids and value:
            return value
    return None


def _image_url(item: dict[str, Any], pictures: list[dict[str, Any]]) -> str | None:
    thumbnail = _optional_str(item.get("secure_thumbnail")) or _optional_str(item.get("thumbnail"))
    if thumbnail:
        return thumbnail
    if pictures:
        first = pictures[0]
        if isinstance(first, dict):
            return _optional_str(first.get("secure_url")) or _optional_str(first.get("url"))
    return None


def _seller_name(seller: dict[str, Any] | None) -> str | None:
    if not seller:
        return None
    return _optional_str(seller.get("nickname"))


def _is_available(item: dict[str, Any]) -> bool:
    status = item.get("status")
    quantity = item.get("available_quantity")
    if status is not None and status != "active":
        return False
    if quantity is None:
        return True
    parsed_quantity = _optional_int(quantity, "available_quantity")
    return parsed_quantity is None or parsed_quantity > 0


def _required_str(payload: dict[str, Any], field_name: str) -> str:
    value = _optional_str(payload.get(field_name))
    if value is None:
        raise MercadoLivreNormalizationError(f"Mercado Livre item field '{field_name}' is required")
    return value


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_currency(value: Any) -> str:
    currency = _optional_str(value)
    if currency is None:
        raise MercadoLivreNormalizationError("Mercado Livre item field 'currency_id' is required")
    if len(currency) != 3:
        raise MercadoLivreNormalizationError("Mercado Livre item field 'currency_id' must be a 3-letter code")
    return currency


def _required_decimal(value: Any, field_name: str) -> Decimal:
    if not _has_value(value):
        raise MercadoLivreNormalizationError(f"Mercado Livre item field '{field_name}' is required")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise MercadoLivreNormalizationError(f"Mercado Livre item field '{field_name}' must be a valid decimal") from exc
    if amount < 0:
        raise MercadoLivreNormalizationError(f"Mercado Livre item field '{field_name}' must be greater than or equal to zero")
    return amount


def _optional_decimal(value: Any, field_name: str = "decimal") -> Decimal | None:
    if not _has_value(value):
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise MercadoLivreNormalizationError(f"Mercado Livre item field '{field_name}' must be a valid decimal") from exc
    if amount < 0:
        raise MercadoLivreNormalizationError(f"Mercado Livre item field '{field_name}' must be greater than or equal to zero")
    return amount


def _optional_int(value: Any, field_name: str = "integer") -> int | None:
    if not _has_value(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise MercadoLivreNormalizationError(f"Mercado Livre item field '{field_name}' must be a valid integer") from exc


def _has_value(value: Any) -> bool:
    return value is not None and (not isinstance(value, str) or value.strip() != "")
