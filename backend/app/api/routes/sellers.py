from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes._domain import call_domain, require_found
from app.database.session import get_db
from app.models.user import User
from app.schemas.seller import SellerCreate, SellerRead, SellerUpdate
from app.services import sellers

router = APIRouter()


@router.get("", response_model=list[SellerRead])
def list_sellers(db: Annotated[Session, Depends(get_db)], limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return sellers.list_sellers(db, limit, offset)


@router.get("/{seller_id}", response_model=SellerRead)
def get_seller(seller_id: int, db: Annotated[Session, Depends(get_db)]):
    return call_domain(lambda: require_found(sellers.get_seller(db, seller_id), "Seller not found"))


@router.post("", response_model=SellerRead, status_code=status.HTTP_201_CREATED)
def create_seller(payload: SellerCreate, db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]):
    return call_domain(lambda: sellers.create_seller(db, payload))


@router.patch("/{seller_id}", response_model=SellerRead)
def update_seller(seller_id: int, payload: SellerUpdate, db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]):
    return call_domain(lambda: sellers.update_seller(db, seller_id, payload))


@router.delete("/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_seller(seller_id: int, db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]):
    call_domain(lambda: sellers.delete_seller(db, seller_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
