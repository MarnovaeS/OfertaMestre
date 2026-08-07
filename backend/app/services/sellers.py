from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions.domain import DomainNotFoundError
from app.models.seller import Seller
from app.schemas.seller import SellerCreate, SellerUpdate
from app.services._persistence import commit_delete, commit_refresh


def list_sellers(db: Session, limit: int, offset: int) -> list[Seller]:
    return list(db.scalars(select(Seller).order_by(Seller.id).limit(limit).offset(offset)))


def get_seller(db: Session, seller_id: int) -> Seller | None:
    return db.get(Seller, seller_id)


def create_seller(db: Session, payload: SellerCreate) -> Seller:
    return commit_refresh(db, Seller(**payload.model_dump()))


def update_seller(db: Session, seller_id: int, payload: SellerUpdate) -> Seller:
    seller = get_seller(db, seller_id)
    if seller is None:
        raise DomainNotFoundError("Seller not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(seller, key, value)
    return commit_refresh(db, seller)


def delete_seller(db: Session, seller_id: int) -> None:
    seller = get_seller(db, seller_id)
    if seller is None:
        raise DomainNotFoundError("Seller not found")
    commit_delete(db, seller)
