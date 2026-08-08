from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.exceptions.domain import DomainConflictError, DomainNotFoundError
from app.ingestion.contracts import ExternalOfferInput, IngestionResult
from app.integrations.mercadolivre.collector import MercadoLivreCollectorService
from app.integrations.mercadolivre.exceptions import (
    MercadoLivreApiError,
    MercadoLivreAuthorizationRevokedError,
    MercadoLivreConfigurationError,
    MercadoLivreForbiddenError,
    MercadoLivreNotFoundError,
    MercadoLivreOAuthError,
    MercadoLivreRateLimitError,
    MercadoLivreServerError,
    MercadoLivreUnauthorizedError,
)
from app.integrations.mercadolivre.schemas import MercadoLivreAuthorizeResponse, MercadoLivreStatusResponse
from app.integrations.mercadolivre.service import create_authorization, disconnect, get_status, handle_callback
from app.models.user import User

router = APIRouter()
callback_router = APIRouter()


@router.get("/authorize", response_model=MercadoLivreAuthorizeResponse)
def authorize_mercadolivre(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MercadoLivreAuthorizeResponse:
    try:
        return create_authorization(db, current_user)
    except MercadoLivreConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from exc


@router.get("/status", response_model=MercadoLivreStatusResponse)
def read_mercadolivre_status(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MercadoLivreStatusResponse:
    return get_status(db, current_user)


@router.get("/items/{item_id}", response_model=ExternalOfferInput)
def read_mercadolivre_item(
    item_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ExternalOfferInput:
    return _call_mercadolivre(lambda: MercadoLivreCollectorService(db, current_user).fetch_normalized_item(item_id))


@router.post("/items/{item_id}/ingest", response_model=IngestionResult, status_code=status.HTTP_201_CREATED)
def ingest_mercadolivre_item(
    item_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> IngestionResult:
    return _call_mercadolivre(lambda: MercadoLivreCollectorService(db, current_user).ingest_item(item_id))


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_mercadolivre(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    disconnect(db, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@callback_router.get("/oauth/mercadolivre/callback")
def mercadolivre_callback(
    code: str,
    state: str,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    try:
        return handle_callback(db, code, state)
    except MercadoLivreConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from exc
    except (MercadoLivreOAuthError, ValidationError) as exc:
        detail = exc.message if isinstance(exc, MercadoLivreOAuthError) else "Invalid Mercado Livre OAuth response"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from exc


def _call_mercadolivre(operation):
    try:
        return operation()
    except MercadoLivreAuthorizationRevokedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc
    except MercadoLivreUnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc
    except MercadoLivreForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message) from exc
    except (MercadoLivreNotFoundError, DomainNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except DomainConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc
    except MercadoLivreRateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=exc.message) from exc
    except MercadoLivreServerError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from exc
    except MercadoLivreApiError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.message) from exc
    except (ValidationError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid Mercado Livre item payload") from exc
