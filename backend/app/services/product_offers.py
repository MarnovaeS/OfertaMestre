from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions.domain import DomainConflictError, DomainNotFoundError
from app.models.product import Product
from app.models.product_offer import ProductOffer
from app.models.seller import Seller
from app.models.store import Store
from app.schemas.product_offer import ProductOfferCreate, ProductOfferUpdate
from app.services._persistence import commit_delete, commit_refresh


def list_product_offers(db: Session, limit: int, offset: int) -> list[ProductOffer]:
    return list(db.scalars(select(ProductOffer).order_by(ProductOffer.id).limit(limit).offset(offset)))


def get_product_offer(db: Session, offer_id: int) -> ProductOffer | None:
    return db.get(ProductOffer, offer_id)


def _validate_offer_references(db: Session, product_id: int, store_id: int, seller_id: int | None) -> None:
    if db.get(Product, product_id) is None:
        raise DomainNotFoundError("Product not found")

    if db.get(Store, store_id) is None:
        raise DomainNotFoundError("Store not found")

    if seller_id is None:
        return

    seller = db.get(Seller, seller_id)
    if seller is None:
        raise DomainNotFoundError("Seller not found")

    if seller.store_id != store_id:
        raise DomainConflictError("Seller does not belong to the offer store")


def create_product_offer(db: Session, payload: ProductOfferCreate) -> ProductOffer:
    _validate_offer_references(db, payload.product_id, payload.store_id, payload.seller_id)
    return commit_refresh(db, ProductOffer(**payload.model_dump()))


def update_product_offer(db: Session, offer_id: int, payload: ProductOfferUpdate) -> ProductOffer:
    offer = get_product_offer(db, offer_id)
    if offer is None:
        raise DomainNotFoundError("Offer not found")

    values = payload.model_dump(exclude_unset=True)
    next_product_id = values.get("product_id", offer.product_id)
    next_store_id = values.get("store_id", offer.store_id)
    next_seller_id = values.get("seller_id", offer.seller_id)

    if {"product_id", "store_id", "seller_id"}.intersection(values):
        _validate_offer_references(db, next_product_id, next_store_id, next_seller_id)

    for key, value in values.items():
        setattr(offer, key, value)
    return commit_refresh(db, offer)


def delete_product_offer(db: Session, offer_id: int) -> None:
    offer = get_product_offer(db, offer_id)
    if offer is None:
        raise DomainNotFoundError("Offer not found")
    commit_delete(db, offer)
