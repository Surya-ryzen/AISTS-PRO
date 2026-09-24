from fastapi import APIRouter, Depends

from backend.app.dependencies.system import get_system
from backend.app.services.system.service import TrafficSystemService
from backend.app.database.tables.user import User
from backend.app.dependencies.auth import get_current_user

router = APIRouter(
    tags=["System Status"],
)


@router.get(
    "/status",
    summary="Get traffic system status",
)
def status(
    system: TrafficSystemService = Depends(get_system),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the current processing status.
    """

    if system.running:

        if system.get_latest_image() is not None:
            state = "RUNNING"
        else:
            state = "STARTING"

    else:
        state = "STOPPED"

    return {
        "state": state,
        "running": system.running,
        "frame_available": (system.get_latest_image() is not None),
    }
