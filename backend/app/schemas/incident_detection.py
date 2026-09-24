from datetime import datetime

from pydantic import BaseModel

from backend.app.services.incident_detection.models import (
    IncidentSeverity,
    IncidentType,
)


class IncidentResponse(BaseModel):
    incident_type: IncidentType
    severity: IncidentSeverity
    track_ids: list[int]
    lane_id: int | None
    confidence: float
    timestamp: datetime
    description: str


class IncidentDetectionResponse(BaseModel):
    incident_detected: bool
    incident_count: int
    incidents: list[IncidentResponse]
