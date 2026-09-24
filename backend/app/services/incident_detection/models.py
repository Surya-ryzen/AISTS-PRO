from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class IncidentType(str, Enum):
    ACCIDENT_SUSPECTED = "ACCIDENT_SUSPECTED"
    SPEED_VIOLATION = "SPEED_VIOLATION"


class IncidentSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class Incident:
    incident_type: IncidentType
    severity: IncidentSeverity
    track_ids: list[int]
    lane_id: int | None
    confidence: float
    timestamp: datetime
    description: str
