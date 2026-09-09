import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions.domain import DomainConflictError, DomainNotFoundError
from app.ingestion.contracts import ExternalOfferInput, IngestionResult
from app.ingestion.matcher import MATCH_CREATED_NEW, match_product
from app.ingestion.normalizer import normalize_offer, normalize_slug
from app.models.brand import Brand
from app.models.category import Category
from app.models.price_snapshot import PriceSnapshot
from app.models.product import Product
from app.models.product_offer import ProductOffer
from app.models.seller import Seller
from app.models.store import Store

logger = logging.getLogger("app.ingestion")


def ingest_external_offer(db: Session, payload: ExternalOfferInput) -> IngestionResult:
    normalized = normalize_offer(payload)
    try:
        result = _ingest_external_offer(db, normalized)
        db.commit()
        logger.info(
            "external_offer_ingested",
            extra={
                "source": normalized.source,
                "store_slug": normalized.store_slug,
                "external_id": normalized.external_id,
                "product_id": result.product_id,
                "offer_id": result.offer_id,
                "matched_by": result.matched_by,
                "snapshot_created": result.snapshot_created,
            },
        )
        return result
    except IntegrityError as exc:
        db.rollback()
        raise DomainConflictError("Ingestion violates a unique constraint") from exc
    except Exception:
        db.rollback()
        raise


def _ingest_external_offer(db: Session, payload: ExternalOfferInput) -> IngestionResult:
    store = _get_store(db, payload.store_slug)
    existing_offer = _get_existing_offer(db, store.id, payload.external_id)
    seller, seller_created = _get_or_create_seller(db, store, payload)
    product, product_created, matched_by = _resolve_product(db, payload, existing_offer)
    offer, offer_created = _get_or_create_offer(db, payload, product, store, seller, existing_offer)
    snapshot_created = _create_snapshot_if_needed(db, offer, payload)

    return IngestionResult(
        product_id=product.id,
        offer_id=offer.id,
        seller_id=seller.id if seller else None,
        product_created=product_created,
        offer_created=offer_created,
        seller_created=seller_created,
        snapshot_created=snapshot_created,
        matched_by=matched_by,
    )


def _get_store(db: Session, store_slug: str) -> Store:
    store = db.scalars(select(Store).where(Store.slug == store_slug)).first()
    if store is None:
        raise DomainNotFoundError("Store not found")
    return store


def _get_existing_offer(db: Session, store_id: int, external_id: str) -> ProductOffer | None:
    return db.scalars(
        select(ProductOffer).where(ProductOffer.store_id == store_id, ProductOffer.external_id == external_id)
    ).first()


def _get_existing_brand(db: Session, brand_name: str | None) -> Brand | None:
    if brand_name is None:
        return None
    return db.scalars(select(Brand).where(Brand.slug == normalize_slug(brand_name))).first()


def _get_or_create_brand(db: Session, brand_name: str | None) -> Brand | None:
    if brand_name is None:
        return None
    slug = normalize_slug(brand_name)
    brand = db.scalars(select(Brand).where(Brand.slug == slug)).first()
    if brand is not None:
        return brand
    brand = Brand(name=brand_name, slug=slug)
    db.add(brand)
    db.flush()
    return brand


def _get_or_create_category(db: Session, category_name: str | None) -> Category | None:
    if category_name is None:
        return None
    slug = normalize_slug(category_name)
    category = db.scalars(select(Category).where(Category.slug == slug)).first()
    if category is not None:
        return category
    category = Category(name=category_name, slug=slug)
    db.add(category)
    db.flush()
    return category


def _get_or_create_seller(db: Session, store: Store, payload: ExternalOfferInput) -> tuple[Seller | None, bool]:
    if payload.seller_external_id is None and payload.seller_name is None:
        return None, False

    seller = None
    if payload.seller_external_id is not None:
        seller = db.scalars(
            select(Seller).where(Seller.store_id == store.id, Seller.external_id == payload.seller_external_id)
        ).first()

    if seller is None and payload.seller_name is not None:
        seller = db.scalars(select(Seller).where(Seller.store_id == store.id, Seller.name == payload.seller_name)).first()

    if seller is not None:
        return seller, False

    seller = Seller(
        store_id=store.id,
        name=payload.seller_name or payload.seller_external_id or "Unknown seller",
        external_id=payload.seller_external_id,
        is_official=bool(payload.seller_is_official),
    )
    db.add(seller)
    db.flush()
    return seller, True


def _resolve_product(
    db: Session,
    payload: ExternalOfferInput,
    existing_offer: ProductOffer | None,
) -> tuple[Product, bool, str]:
    existing_brand = _get_existing_brand(db, payload.brand_name)
    product_match = match_product(
        db,
        product_name=payload.product_name,
        brand=existing_brand,
        model=payload.model,
        gtin=payload.gtin,
        sku=payload.sku,
    )

    if existing_offer is not None:
        if product_match.product is not None and product_match.product.id != existing_offer.product_id:
            raise DomainConflictError("Existing offer is linked to a different product")
        return existing_offer.product, False, product_match.matched_by

    if product_match.product is not None:
        return product_match.product, False, product_match.matched_by

    brand = _get_or_create_brand(db, payload.brand_name)
    category = _get_or_create_category(db, payload.category_name)
    product = Product(
        brand_id=brand.id if brand else None,
        category_id=category.id if category else None,
        name=payload.product_name,
        slug=_unique_product_slug(db, payload.product_name),
        model=payload.model,
        gtin=payload.gtin,
        sku=payload.sku,
        image_url=payload.image_url,
        is_active=True,
    )
    db.add(product)
    db.flush()
    return product, True, MATCH_CREATED_NEW


def _unique_product_slug(db: Session, product_name: str) -> str:
    base_slug = normalize_slug(product_name)
    slug = base_slug
    suffix = 2
    while db.scalars(select(Product.id).where(Product.slug == slug)).first() is not None:
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    return slug


def _get_or_create_offer(
    db: Session,
    payload: ExternalOfferInput,
    product: Product,
    store: Store,
    seller: Seller | None,
    existing_offer: ProductOffer | None,
) -> tuple[ProductOffer, bool]:
    if existing_offer is None:
        offer = ProductOffer(
            product_id=product.id,
            store_id=store.id,
            seller_id=seller.id if seller else None,
            external_id=payload.external_id,
            url=payload.url,
            title=payload.title,
            current_price=payload.current_price,
            original_price=payload.original_price,
            shipping_price=payload.shipping_price,
            currency=payload.currency,
            is_available=payload.is_available,
            is_prime=payload.is_prime,
            is_free_shipping=payload.is_free_shipping,
            installment_count=payload.installment_count,
            installment_value=payload.installment_value,
            last_checked_at=payload.captured_at,
        )
        db.add(offer)
        db.flush()
        return offer, True

    offer = existing_offer
    offer.seller_id = seller.id if seller else None
    offer.url = payload.url
    offer.title = payload.title
    offer.current_price = payload.current_price
    offer.original_price = payload.original_price
    offer.shipping_price = payload.shipping_price
    offer.currency = payload.currency
    offer.is_available = payload.is_available
    offer.is_prime = payload.is_prime
    offer.is_free_shipping = payload.is_free_shipping
    offer.installment_count = payload.installment_count
    offer.installment_value = payload.installment_value
    offer.last_checked_at = payload.captured_at
    db.flush()
    return offer, False


def _create_snapshot_if_needed(db: Session, offer: ProductOffer, payload: ExternalOfferInput) -> bool:
    latest = db.scalars(
        select(PriceSnapshot)
        .where(PriceSnapshot.product_offer_id == offer.id)
        .order_by(PriceSnapshot.captured_at.desc(), PriceSnapshot.id.desc())
    ).first()

    if latest is not None and _same_prices(latest, payload):
        return False

    values = {
        "product_offer_id": offer.id,
        "price": payload.current_price,
        "original_price": payload.original_price,
        "shipping_price": payload.shipping_price,
        "price_source": payload.price_source,
        "price_source_class": payload.price_source_class,
    }
    if payload.captured_at is not None:
        values["captured_at"] = payload.captured_at
    snapshot = PriceSnapshot(**values)
    db.add(snapshot)
    db.flush()
    return True


def _same_prices(snapshot: PriceSnapshot, payload: ExternalOfferInput) -> bool:
    return (
        _decimal_or_none(snapshot.price) == _decimal_or_none(payload.current_price)
        and _decimal_or_none(snapshot.original_price) == _decimal_or_none(payload.original_price)
        and _decimal_or_none(snapshot.shipping_price) == _decimal_or_none(payload.shipping_price)
        and snapshot.price_source == payload.price_source
        and snapshot.price_source_class == payload.price_source_class
    )


def _decimal_or_none(value: Decimal | None) -> Decimal | None:
    return None if value is None else Decimal(value).quantize(Decimal("0.01"))
