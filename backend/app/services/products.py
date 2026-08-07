from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions.domain import DomainNotFoundError
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.services._persistence import commit_delete, commit_refresh


def list_products(db: Session, limit: int, offset: int) -> list[Product]:
    return list(db.scalars(select(Product).order_by(Product.id).limit(limit).offset(offset)))


def get_product(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def create_product(db: Session, payload: ProductCreate) -> Product:
    return commit_refresh(db, Product(**payload.model_dump()))


def update_product(db: Session, product_id: int, payload: ProductUpdate) -> Product:
    product = get_product(db, product_id)
    if product is None:
        raise DomainNotFoundError("Product not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    return commit_refresh(db, product)


def delete_product(db: Session, product_id: int) -> None:
    product = get_product(db, product_id)
    if product is None:
        raise DomainNotFoundError("Product not found")
    commit_delete(db, product)
