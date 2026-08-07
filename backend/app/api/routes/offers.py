from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes._domain import call_domain, require_found
from app.database.session import get_db
from app.models.user import User
from app.schemas.price_snapshot import PriceSnapshotCreate, PriceSnapshotRead
from app.schemas.product_offer import ProductOfferCreate, ProductOfferRead, ProductOfferUpdate
from app.services import price_snapshots, product_offers

router = APIRouter()


@router.get("", response_model=list[ProductOfferRead])
def list_offers(db: Annotated[Session, Depends(get_db)], limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return product_offers.list_product_offers(db, limit, offset)


@router.get("/{offer_id}", response_model=ProductOfferRead)
def get_offer(offer_id: int, db: Annotated[Session, Depends(get_db)]):
    return call_domain(lambda: require_found(product_offers.get_product_offer(db, offer_id), "Offer not found"))


@router.post("", response_model=ProductOfferRead, status_code=status.HTTP_201_CREATED)
def create_offer(payload: ProductOfferCreate, db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]):
    return call_domain(lambda: product_offers.create_product_offer(db, payload))


@router.patch("/{offer_id}", response_model=ProductOfferRead)
def update_offer(offer_id: int, payload: ProductOfferUpdate, db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]):
    return call_domain(lambda: product_offers.update_product_offer(db, offer_id, payload))


@router.delete("/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_offer(offer_id: int, db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]):
    call_domain(lambda: product_offers.delete_product_offer(db, offer_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{offer_id}/price-history", response_model=list[PriceSnapshotRead])
def get_price_history(offer_id: int, db: Annotated[Session, Depends(get_db)]):
    call_domain(lambda: require_found(product_offers.get_product_offer(db, offer_id), "Offer not found"))
    return price_snapshots.list_price_snapshots(db, offer_id)


@router.post("/{offer_id}/price-history", response_model=PriceSnapshotRead, status_code=status.HTTP_201_CREATED)
def create_price_snapshot(
    offer_id: int,
    payload: PriceSnapshotCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    return call_domain(lambda: price_snapshots.create_price_snapshot(db, offer_id, payload))
