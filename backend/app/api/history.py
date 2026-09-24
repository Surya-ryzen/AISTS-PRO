from fastapi import APIRouter, Depends, Query

from backend.app.database.session_manager import get_db_session
from backend.app.services.persistence.service import PersistenceService
from backend.app.database.tables.user import User
from backend.app.dependencies.auth import get_current_user

from backend.app.schemas.history import (
    TrafficHistoryResponse,
    LaneHistoryResponse,
    SignalHistoryResponse,
)

router = APIRouter(
    prefix="/history",
    tags=["History"],
)


persistence = PersistenceService()


@router.get(
    "/traffic",
    response_model=list[TrafficHistoryResponse],
    summary="Get traffic analytics history",
)
def traffic_history(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    current_user: User = Depends(get_current_user),
):
    """
    Returns historical traffic analytics.
    """

    with get_db_session() as session:

        return persistence.get_traffic_history(
            session,
            limit,
        )


@router.get(
    "/lanes",
    response_model=list[LaneHistoryResponse],
    summary="Get lane analytics history",
)
def lane_history(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    current_user: User = Depends(get_current_user),
):
    """
    Returns historical lane analytics.
    """

    with get_db_session() as session:

        return persistence.get_lane_history(
            session,
            limit,
        )


@router.get(
    "/signals",
    response_model=list[SignalHistoryResponse],
    summary="Get signal decision history",
)
def signal_history(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    current_user: User = Depends(get_current_user),
):
    """
    Returns historical traffic signal decisions.
    """

    with get_db_session() as session:

        return persistence.get_signal_history(
            session,
            limit,
        )
