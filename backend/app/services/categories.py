from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions.domain import DomainNotFoundError
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services._persistence import commit_delete, commit_refresh


def list_categories(db: Session, limit: int, offset: int) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.id).limit(limit).offset(offset)))


def get_category(db: Session, category_id: int) -> Category | None:
    return db.get(Category, category_id)


def create_category(db: Session, payload: CategoryCreate) -> Category:
    return commit_refresh(db, Category(**payload.model_dump()))


def update_category(db: Session, category_id: int, payload: CategoryUpdate) -> Category:
    category = get_category(db, category_id)
    if category is None:
        raise DomainNotFoundError("Category not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    return commit_refresh(db, category)


def delete_category(db: Session, category_id: int) -> None:
    category = get_category(db, category_id)
    if category is None:
        raise DomainNotFoundError("Category not found")
    commit_delete(db, category)
