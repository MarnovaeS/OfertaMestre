from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions.domain import DomainNotFoundError
from app.models.store import Store
from app.schemas.store import StoreCreate, StoreUpdate
from app.services._persistence import commit_delete, commit_refresh


def list_stores(db: Session, limit: int, offset: int) -> list[Store]:
    return list(db.scalars(select(Store).order_by(Store.id).limit(limit).offset(offset)))


def get_store(db: Session, store_id: int) -> Store | None:
    return db.get(Store, store_id)


def create_store(db: Session, payload: StoreCreate) -> Store:
    return commit_refresh(db, Store(**payload.model_dump()))


def update_store(db: Session, store_id: int, payload: StoreUpdate) -> Store:
    store = get_store(db, store_id)
    if store is None:
        raise DomainNotFoundError("Store not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(store, key, value)
    return commit_refresh(db, store)


def delete_store(db: Session, store_id: int) -> None:
    store = get_store(db, store_id)
    if store is None:
        raise DomainNotFoundError("Store not found")
    commit_delete(db, store)
