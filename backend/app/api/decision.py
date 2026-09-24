from fastapi import APIRouter, Depends, HTTPException
from backend.app.dependencies.system import get_system
from backend.app.services.system.service import TrafficSystemService
from backend.app.schemas.decision import DecisionResponse
from backend.app.dependencies.auth import require_admin
from backend.app.database.tables.user import User

router = APIRouter(
    tags=["AI Decision"],
)


@router.get(
    "/decision",
    summary="Get the latest AI traffic decision",
    response_model=DecisionResponse,
)
def decision(
    system: TrafficSystemService = Depends(get_system),
    current_user: User = Depends(require_admin),
):

    latest = system.decision.last_decision

    if latest is None:

        raise HTTPException(status_code=503, detail="No decision available yet. Wait for traffic measurements and a configured road.")

    return DecisionResponse(
        selected_lane=latest.selected_lane,
        green_time=latest.green_time,
        reason=latest.reason,
    )
