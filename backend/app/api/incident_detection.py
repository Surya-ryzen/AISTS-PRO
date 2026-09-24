from fastapi import APIRouter, Depends

from backend.app.dependencies.auth import get_current_user
from backend.app.dependencies.system import get_system
from backend.app.database.tables.user import User
from backend.app.schemas.incident_detection import (
    IncidentDetectionResponse,
    IncidentResponse,
)
from backend.app.services.system.service import TrafficSystemService

router = APIRouter(
    prefix="/incident-detection",
    tags=["Incident Detection"],
)


@router.get(
    "",
    response_model=IncidentDetectionResponse,
    summary="Get current incident detection status",
)
def get_incident_detection(
    system: TrafficSystemService = Depends(get_system),
    current_user: User = Depends(get_current_user),
):
    incidents = system.latest_result.incidents if system.latest_result else []

    return IncidentDetectionResponse(
        incident_detected=len(incidents) > 0,
        incident_count=len(incidents),
        incidents=[
            IncidentResponse(
                incident_type=incident.incident_type,
                severity=incident.severity,
                track_ids=incident.track_ids,
                lane_id=incident.lane_id,
                confidence=incident.confidence,
                timestamp=incident.timestamp,
                description=incident.description,
            )
            for incident in incidents
        ],
    )
