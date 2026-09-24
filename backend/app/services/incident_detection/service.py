from backend.app.services.incident_detection.config import IncidentDetectionConfig
from backend.app.services.incident_detection.detectors import (
    AccidentDetector,
    SpeedViolationDetector,
)
from backend.app.services.incident_detection.models import Incident


class IncidentDetectionService:
    """
    Coordinates all incident detection modules.
    """

    def __init__(self):
        self.config = IncidentDetectionConfig()

        self.speed_violation_detector = SpeedViolationDetector(
            speed_limit_kmh=self.config.speed_limit_kmh,
            tolerance_kmh=self.config.speed_tolerance_kmh,
        )

        self.accident_detector = AccidentDetector()

    def process(
        self,
        tracks,
        speeds,
        behavior_events,
    ) -> list[Incident]:

        incidents = []

        # ---------------------------------
        # Speed Violations
        # ---------------------------------

        if self.config.speed_violation_enabled:

            for speed in speeds:

                track = next(
                    (track for track in tracks if track.track_id == speed.track_id),
                    None,
                )

                if track is None:
                    continue

                incident = self.speed_violation_detector.detect(
                    track_id=speed.track_id,
                    speed_kmh=speed.speed_kmh,
                    lane_id=track.lane_id,
                )

                if incident is not None:
                    incidents.append(incident)

        # ---------------------------------
        # Accident Detection
        # ---------------------------------

        if self.config.accident_enabled:

            accident_incidents = self.accident_detector.detect(
                tracks=tracks,
                speeds=speeds,
                behavior_events=behavior_events,
            )

            incidents.extend(accident_incidents)

        return incidents
