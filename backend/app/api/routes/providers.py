from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.providers.schemas import ProviderIntegrationStatus
from app.providers.service import list_provider_statuses

router = APIRouter()


@router.get("", response_model=list[ProviderIntegrationStatus])
def read_provider_statuses(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ProviderIntegrationStatus]:
    return list_provider_statuses(db, current_user)
