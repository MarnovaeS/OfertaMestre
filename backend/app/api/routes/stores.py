from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes._domain import call_domain, require_found
from app.database.session import get_db
from app.models.user import User
from app.schemas.store import StoreCreate, StoreRead, StoreUpdate
from app.services import stores

router = APIRouter()


@router.get("", response_model=list[StoreRead])
def list_stores(db: Annotated[Session, Depends(get_db)], limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return stores.list_stores(db, limit, offset)


@router.get("/{store_id}", response_model=StoreRead)
def get_store(store_id: int, db: Annotated[Session, Depends(get_db)]):
    return call_domain(lambda: require_found(stores.get_store(db, store_id), "Store not found"))


@router.post("", response_model=StoreRead, status_code=status.HTTP_201_CREATED)
def create_store(payload: StoreCreate, db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]):
    return call_domain(lambda: stores.create_store(db, payload))


@router.patch("/{store_id}", response_model=StoreRead)
def update_store(store_id: int, payload: StoreUpdate, db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]):
    return call_domain(lambda: stores.update_store(db, store_id, payload))


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_store(store_id: int, db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]):
    call_domain(lambda: stores.delete_store(db, store_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
