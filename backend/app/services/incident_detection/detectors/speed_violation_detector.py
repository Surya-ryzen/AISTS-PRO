from datetime import datetime, timezone

from backend.app.services.incident_detection.models import (
    Incident,
    IncidentSeverity,
    IncidentType,
)


class SpeedViolationDetector:
    """
    Detects vehicles exceeding the configured speed limit.
    """

    def __init__(
        self,
        speed_limit_kmh: float,
        tolerance_kmh: float = 0.0,
    ):
        self.speed_limit_kmh = speed_limit_kmh
        self.tolerance_kmh = tolerance_kmh

    def detect(
        self,
        track_id: int,
        speed_kmh: float,
        lane_id: int | None = None,
    ) -> Incident | None:
        threshold = self.speed_limit_kmh + self.tolerance_kmh

        if speed_kmh <= threshold:
            return None

        excess_speed = speed_kmh - self.speed_limit_kmh

        if excess_speed >= 20:
            severity = IncidentSeverity.HIGH
        elif excess_speed >= 10:
            severity = IncidentSeverity.MEDIUM
        else:
            severity = IncidentSeverity.LOW

        return Incident(
            incident_type=IncidentType.SPEED_VIOLATION,
            severity=severity,
            track_ids=[track_id],
            lane_id=lane_id,
            confidence=1.0,
            timestamp=datetime.now(timezone.utc),
            description=(
                f"Vehicle exceeded the speed limit. "
                f"Measured speed: {speed_kmh:.2f} km/h, "
                f"speed limit: {self.speed_limit_kmh:.2f} km/h."
            ),
        )
