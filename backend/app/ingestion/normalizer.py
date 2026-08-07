import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit

from app.ingestion.contracts import ExternalOfferInput

_SPACES_RE = re.compile(r"\s+")
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = _SPACES_RE.sub(" ", value.strip())
    return cleaned or None


def normalize_currency(value: str) -> str:
    return clean_text(value).upper() if clean_text(value) else "BRL"


def normalize_url(value: str | None) -> str | None:
    cleaned = clean_text(value)
    if cleaned is None:
        return None
    parts = urlsplit(cleaned)
    scheme = parts.scheme.lower() or "https"
    netloc = parts.netloc.lower()
    path = parts.path or ""
    return urlunsplit((scheme, netloc, path, parts.query, ""))


def normalize_slug(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = _SLUG_RE.sub("-", ascii_value.lower()).strip("-")
    return slug or "item"


def normalize_name(value: str | None) -> str | None:
    cleaned = clean_text(value)
    if cleaned is None:
        return None
    return cleaned.title()


def normalize_identifier(value: str | None) -> str | None:
    cleaned = clean_text(value)
    return cleaned.upper() if cleaned else None


def normalize_offer(payload: ExternalOfferInput) -> ExternalOfferInput:
    values = payload.model_dump()
    values["source"] = clean_text(payload.source).lower()
    values["external_id"] = clean_text(payload.external_id)
    values["store_slug"] = normalize_slug(payload.store_slug)
    values["seller_external_id"] = clean_text(payload.seller_external_id)
    values["seller_name"] = normalize_name(payload.seller_name)
    values["title"] = clean_text(payload.title)
    values["product_name"] = clean_text(payload.product_name)
    values["brand_name"] = normalize_name(payload.brand_name)
    values["category_name"] = normalize_name(payload.category_name)
    values["model"] = clean_text(payload.model)
    values["gtin"] = normalize_identifier(payload.gtin)
    values["sku"] = normalize_identifier(payload.sku)
    values["url"] = normalize_url(payload.url)
    values["image_url"] = normalize_url(payload.image_url)
    values["currency"] = normalize_currency(payload.currency)
    return ExternalOfferInput(**values)
