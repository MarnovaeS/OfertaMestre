from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes._domain import call_domain, require_found
from app.database.session import get_db
from app.models.user import User
from app.schemas.brand import BrandCreate, BrandRead, BrandUpdate
from app.services import brands

router = APIRouter()


@router.get("", response_model=list[BrandRead])
def list_brands(db: Annotated[Session, Depends(get_db)], limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return brands.list_brands(db, limit, offset)


@router.get("/{brand_id}", response_model=BrandRead)
def get_brand(brand_id: int, db: Annotated[Session, Depends(get_db)]):
    return call_domain(lambda: require_found(brands.get_brand(db, brand_id), "Brand not found"))


@router.post("", response_model=BrandRead, status_code=status.HTTP_201_CREATED)
def create_brand(payload: BrandCreate, db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]):
    return call_domain(lambda: brands.create_brand(db, payload))


@router.patch("/{brand_id}", response_model=BrandRead)
def update_brand(brand_id: int, payload: BrandUpdate, db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]):
    return call_domain(lambda: brands.update_brand(db, brand_id, payload))


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brand(brand_id: int, db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]):
    call_domain(lambda: brands.delete_brand(db, brand_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)

