from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions.domain import DomainNotFoundError
from app.models.product_offer import ProductOffer
from app.schemas.product_offer import ProductOfferCreate, ProductOfferUpdate
from app.services._persistence import commit_delete, commit_refresh


def list_product_offers(db: Session, limit: int, offset: int) -> list[ProductOffer]:
    return list(db.scalars(select(ProductOffer).order_by(ProductOffer.id).limit(limit).offset(offset)))


def get_product_offer(db: Session, offer_id: int) -> ProductOffer | None:
    return db.get(ProductOffer, offer_id)


def create_product_offer(db: Session, payload: ProductOfferCreate) -> ProductOffer:
    return commit_refresh(db, ProductOffer(**payload.model_dump()))


def update_product_offer(db: Session, offer_id: int, payload: ProductOfferUpdate) -> ProductOffer:
    offer = get_product_offer(db, offer_id)
    if offer is None:
        raise DomainNotFoundError("Offer not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(offer, key, value)
    return commit_refresh(db, offer)


def delete_product_offer(db: Session, offer_id: int) -> None:
    offer = get_product_offer(db, offer_id)
    if offer is None:
        raise DomainNotFoundError("Offer not found")
    commit_delete(db, offer)
