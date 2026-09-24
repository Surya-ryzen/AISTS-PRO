from fastapi import APIRouter, Depends, HTTPException

from backend.app.dependencies.system import get_system
from backend.app.services.system.service import TrafficSystemService
from backend.app.schemas.signal import SignalResponse
from backend.app.database.tables.user import User
from backend.app.dependencies.auth import get_current_user

router = APIRouter(
    tags=["Traffic Signal"],
)


@router.get(
    "/signal",
    summary="Get current traffic signal state",
    response_model=SignalResponse,
)
def signal(
    system: TrafficSystemService = Depends(get_system),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the current traffic signal state.
    """

    result = system.get_latest_result()

    if result is None:
        raise HTTPException(
            status_code=503,
            detail="Traffic system is starting...",
        )

    signal = result.signal

    return SignalResponse(
        current_green_lane=signal.current_green_lane,
        state=signal.state.value,
        remaining_time=signal.remaining_time,
        green_time=signal.green_time,
        last_reason=signal.last_reason,
    )
