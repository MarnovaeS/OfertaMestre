from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.integrations.amazon.exceptions import AmazonApiError, AmazonConfigurationError, AmazonForbiddenError, AmazonRateLimitError, AmazonServerError, AmazonUnauthorizedError
from app.integrations.amazon.schemas import AmazonItemRead, AmazonStatusResponse
from app.integrations.amazon.service import get_status, search_items
from app.models.user import User

router = APIRouter()


@router.get("/status", response_model=AmazonStatusResponse)
def read_status(db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]) -> AmazonStatusResponse:
    return get_status(db)


@router.get("/search", response_model=list[AmazonItemRead])
def search(keywords: str = Query(min_length=2, max_length=200), item_count: int = Query(10, ge=1, le=10), _: User = Depends(get_current_user)) -> list[AmazonItemRead]:
    try:
        return search_items(keywords, item_count=item_count)
    except AmazonConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from exc
    except AmazonUnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc
    except AmazonForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message) from exc
    except AmazonRateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=exc.message) from exc
    except AmazonServerError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from exc
    except AmazonApiError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.message) from exc
