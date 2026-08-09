from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.exceptions.domain import DomainNotFoundError
from app.integrations.steam.exceptions import (
    SteamApiError,
    SteamConfigurationError,
    SteamForbiddenError,
    SteamRateLimitError,
    SteamServerError,
    SteamUnauthorizedError,
)
from app.integrations.steam.schemas import SteamAppRead, SteamStatusResponse, SteamSyncResult
from app.integrations.steam.service import get_status, list_apps, sync_catalog
from app.models.user import User

router = APIRouter()


@router.get("/status", response_model=SteamStatusResponse)
def read_steam_status(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> SteamStatusResponse:
    return get_status(db)


@router.get("/apps", response_model=list[SteamAppRead])
def read_steam_apps(
    _: Annotated[User, Depends(get_current_user)],
    max_results: int = Query(100, ge=1, le=500),
    last_appid: int | None = Query(None, ge=0),
    modified_since: int | None = Query(None, ge=0),
    include_games: bool = True,
    include_dlc: bool = False,
) -> list[SteamAppRead]:
    return _call_steam(
        lambda: list_apps(
            max_results=max_results,
            last_appid=last_appid,
            modified_since=modified_since,
            include_games=include_games,
            include_dlc=include_dlc,
        )
    )


@router.post("/sync", response_model=SteamSyncResult)
def sync_steam_catalog(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    max_results: int = Query(100, ge=1, le=500),
    last_appid: int | None = Query(None, ge=0),
    modified_since: int | None = Query(None, ge=0),
    include_games: bool = True,
    include_dlc: bool = False,
) -> SteamSyncResult:
    return _call_steam(
        lambda: sync_catalog(
            db,
            max_results=max_results,
            last_appid=last_appid,
            modified_since=modified_since,
            include_games=include_games,
            include_dlc=include_dlc,
        )
    )


def _call_steam(operation):
    try:
        return operation()
    except SteamConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from exc
    except SteamUnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc
    except SteamForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message) from exc
    except DomainNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except SteamRateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=exc.message) from exc
    except SteamServerError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from exc
    except SteamApiError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.message) from exc
