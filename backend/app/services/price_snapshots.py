from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions.domain import DomainNotFoundError
from app.models.price_snapshot import PriceSnapshot
from app.models.product_offer import ProductOffer
from app.schemas.price_snapshot import PriceSnapshotCreate
from app.services._persistence import commit_refresh


def list_price_snapshots(db: Session, offer_id: int) -> list[PriceSnapshot]:
    return list(
        db.scalars(
            select(PriceSnapshot)
            .where(PriceSnapshot.product_offer_id == offer_id)
            .order_by(PriceSnapshot.captured_at, PriceSnapshot.id)
        )
    )


def create_price_snapshot(db: Session, offer_id: int, payload: PriceSnapshotCreate) -> PriceSnapshot:
    if db.get(ProductOffer, offer_id) is None:
        raise DomainNotFoundError("Offer not found")
    values = payload.model_dump(exclude_none=True)
    snapshot = PriceSnapshot(product_offer_id=offer_id, **values)
    return commit_refresh(db, snapshot)
