from fastapi import APIRouter, Depends

from backend.app.database.session_manager import get_db_session
from backend.app.schemas.camera import CameraResponse
from backend.app.services.persistence.service import PersistenceService
from backend.app.database.tables.user import User
from backend.app.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/cameras",
    tags=["Cameras"],
)


persistence = PersistenceService()


@router.get(
    "",
    response_model=list[CameraResponse],
    summary="Get all cameras",
)
def get_cameras(
    current_user: User = Depends(get_current_user),
):
    """
    Returns all configured cameras.
    """

    with get_db_session() as session:

        return persistence.get_cameras(session)
