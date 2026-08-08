from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import PlainTextResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.integrations.mercadolivre.exceptions import MercadoLivreConfigurationError, MercadoLivreOAuthError
from app.integrations.mercadolivre.schemas import MercadoLivreAuthorizeResponse, MercadoLivreStatusResponse
from app.integrations.mercadolivre.service import create_authorization, disconnect, get_status, handle_callback, handle_callback_denial
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


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_mercadolivre(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    disconnect(db, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@callback_router.get("/oauth/mercadolivre/callback", response_class=PlainTextResponse)
def mercadolivre_callback(
    db: Annotated[Session, Depends(get_db)],
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> PlainTextResponse:
    try:
        if error:
            if error == "access_denied":
                handle_callback_denial(db, state)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mercado Livre rejected the OAuth authorization")
        if not state:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mercado Livre OAuth state is required")
        if not code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mercado Livre OAuth authorization code is required")
        return PlainTextResponse(handle_callback(db, code, state))
    except MercadoLivreConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from exc
    except (MercadoLivreOAuthError, ValidationError) as exc:
        detail = exc.message if isinstance(exc, MercadoLivreOAuthError) else "Invalid Mercado Livre OAuth response"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from exc
