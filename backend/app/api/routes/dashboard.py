from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.dashboard import DashboardSummary

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def get_summary(_: Annotated[User, Depends(get_current_user)]) -> DashboardSummary:
    return DashboardSummary(
        deals_today=0,
        excellent_deals=0,
        monitored_products=0,
        alerts_sent=0,
        online_stores=0,
    )

