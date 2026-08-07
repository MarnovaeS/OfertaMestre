from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.normalizer import normalize_slug
from app.models.brand import Brand
from app.models.product import Product

MATCH_GTIN = "gtin"
MATCH_SKU_BRAND = "sku_brand"
MATCH_BRAND_MODEL = "brand_model"
MATCH_NORMALIZED_NAME = "normalized_name"
MATCH_CREATED_NEW = "created_new"


@dataclass(frozen=True)
class ProductMatch:
    product: Product | None
    matched_by: str


def match_product(
    db: Session,
    *,
    product_name: str,
    brand: Brand | None,
    model: str | None,
    gtin: str | None,
    sku: str | None,
) -> ProductMatch:
    if gtin:
        product = db.scalars(select(Product).where(Product.gtin == gtin).order_by(Product.id)).first()
        if product is not None:
            return ProductMatch(product=product, matched_by=MATCH_GTIN)

    if sku and brand is not None:
        product = db.scalars(
            select(Product).where(Product.sku == sku, Product.brand_id == brand.id).order_by(Product.id)
        ).first()
        if product is not None:
            return ProductMatch(product=product, matched_by=MATCH_SKU_BRAND)

    if brand is not None and model:
        product = db.scalars(
            select(Product).where(Product.brand_id == brand.id, Product.model == model).order_by(Product.id)
        ).first()
        if product is not None:
            return ProductMatch(product=product, matched_by=MATCH_BRAND_MODEL)

    slug = normalize_slug(product_name)
    product = db.scalars(select(Product).where(Product.slug == slug).order_by(Product.id)).first()
    if product is not None:
        return ProductMatch(product=product, matched_by=MATCH_NORMALIZED_NAME)

    return ProductMatch(product=None, matched_by=MATCH_CREATED_NEW)
