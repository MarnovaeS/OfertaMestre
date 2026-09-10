from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.integrations.awin.exceptions import (
    AwinApiError,
    AwinConfigurationError,
    AwinForbiddenError,
    AwinRateLimitError,
    AwinServerError,
    AwinUnauthorizedError,
)
from app.integrations.awin.schemas import AwinProgramRead, AwinPromotionRead, AwinStatusResponse
from app.integrations.awin.service import get_status, list_programs, list_promotions
from app.models.user import User

router = APIRouter()


@router.get("/status", response_model=AwinStatusResponse)
def read_status(_: Annotated[User, Depends(get_current_user)]) -> AwinStatusResponse:
    return get_status()


@router.get("/programs", response_model=list[AwinProgramRead])
def read_programs(
    _: Annotated[User, Depends(get_current_user)],
    country_code: str = Query("BR", min_length=2, max_length=2, pattern="^[A-Za-z]{2}$"),
    relationship: Literal["joined", "pending", "suspended", "rejected", "notjoined"] = "joined",
) -> list[AwinProgramRead]:
    return _call_awin(lambda: list_programs(country_code=country_code, relationship=relationship))


@router.get("/promotions", response_model=list[AwinPromotionRead])
def read_promotions(
    _: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=10, le=200),
    membership: Literal["joined", "notJoined", "all"] = "joined",
    promotion_status: Literal["active", "expiringSoon", "upcoming"] = "active",
    promotion_type: Literal["promotion", "voucher", "all"] = "all",
    region_code: str = Query("BR", min_length=2, max_length=2, pattern="^[A-Za-z]{2}$"),
    advertiser_id: int | None = Query(None, ge=1),
) -> list[AwinPromotionRead]:
    return _call_awin(
        lambda: list_promotions(
            page=page,
            page_size=page_size,
            membership=membership,
            status=promotion_status,
            promotion_type=promotion_type,
            region_code=region_code,
            advertiser_id=advertiser_id,
        )
    )


def _call_awin(operation):
    try:
        return operation()
    except AwinConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from exc
    except AwinUnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc
    except AwinForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message) from exc
    except AwinRateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=exc.message) from exc
    except AwinServerError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from exc
    except AwinApiError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.message) from exc
