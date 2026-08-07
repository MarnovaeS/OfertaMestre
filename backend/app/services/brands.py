from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions.domain import DomainNotFoundError
from app.models.brand import Brand
from app.schemas.brand import BrandCreate, BrandUpdate
from app.services._persistence import commit_delete, commit_refresh


def list_brands(db: Session, limit: int, offset: int) -> list[Brand]:
    return list(db.scalars(select(Brand).order_by(Brand.id).limit(limit).offset(offset)))


def get_brand(db: Session, brand_id: int) -> Brand | None:
    return db.get(Brand, brand_id)


def create_brand(db: Session, payload: BrandCreate) -> Brand:
    return commit_refresh(db, Brand(**payload.model_dump()))


def update_brand(db: Session, brand_id: int, payload: BrandUpdate) -> Brand:
    brand = get_brand(db, brand_id)
    if brand is None:
        raise DomainNotFoundError("Brand not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(brand, key, value)
    return commit_refresh(db, brand)


def delete_brand(db: Session, brand_id: int) -> None:
    brand = get_brand(db, brand_id)
    if brand is None:
        raise DomainNotFoundError("Brand not found")
    commit_delete(db, brand)
