from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes._domain import call_domain
from app.database.session import get_db
from app.ingestion.contracts import ExternalOfferInput, IngestionResult
from app.ingestion.service import ingest_external_offer
from app.models.user import User

router = APIRouter()


@router.post("/offers", response_model=IngestionResult, status_code=status.HTTP_201_CREATED)
def ingest_offer(
    payload: ExternalOfferInput,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> IngestionResult:
    return call_domain(lambda: ingest_external_offer(db, payload))
