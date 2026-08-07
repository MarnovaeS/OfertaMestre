from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes._domain import call_domain, require_found
from app.database.session import get_db
from app.models.user import User
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services import products

router = APIRouter()


@router.get("", response_model=list[ProductRead])
def list_products(db: Annotated[Session, Depends(get_db)], limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return products.list_products(db, limit, offset)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Annotated[Session, Depends(get_db)]):
    return call_domain(lambda: require_found(products.get_product(db, product_id), "Product not found"))


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]):
    return call_domain(lambda: products.create_product(db, payload))


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(product_id: int, payload: ProductUpdate, db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]):
    return call_domain(lambda: products.update_product(db, product_id, payload))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]):
    call_domain(lambda: products.delete_product(db, product_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
