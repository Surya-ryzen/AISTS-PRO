from datetime import datetime, timezone

from sqlalchemy.orm import Session

from sqlalchemy import select
from backend.app.database.tables.camera import Camera
from backend.app.database.tables.lane_analytics import LaneAnalytics
from backend.app.database.tables.signal_decision import SignalDecision
from backend.app.database.tables.traffic_analytics import TrafficAnalytics
from backend.app.database.tables.vehicle_event import VehicleEvent

from backend.app.services.analytics.models import TrafficStatistics
from backend.app.services.lane_analytics.models import LaneStatistics
from backend.app.services.tracking.models import Track
from backend.app.services.decision_engine.models import Decision
from backend.app.database.tables.camera import Camera


class PersistenceService:
    """
    Handles persistence of traffic system data.
    """

    def get_active_camera(
        self,
        session: Session,
    ) -> Camera | None:
        """
        Returns the currently active camera.
        """

        statement = (
            select(Camera)
            .where(Camera.is_active.is_(True))
            .order_by(Camera.id.asc())
            .limit(1)
        )

        return session.scalars(statement).first()

    def update_camera_source(
        self,
        session: Session,
        camera_id: int,
        source: str,
        source_type: str,
    ) -> Camera | None:
        """
        Updates the source configuration of a camera.
        """

        camera = session.get(Camera, camera_id)

        if camera is None:
            return None

        camera.source = source
        camera.source_type = source_type

        return camera

    def get_active_camera_source(
        self,
        session: Session,
    ) -> tuple[str, str] | None:
        """
        Returns the source and source type
        of the active camera.
        """

        camera = self.get_active_camera(session)

        if camera is None:
            return None

        return camera.source, camera.source_type

    def get_cameras(
        self,
        session: Session,
    ) -> list[Camera]:
        """
        Returns all configured cameras.
        """

        statement = select(Camera).order_by(Camera.id.asc())

        return list(session.scalars(statement).all())

    def get_cameras_by_junction(
        self,
        session: Session,
        junction_id: int,
    ) -> list[Camera]:
        """
        Returns all cameras belonging to a junction.
        """

        statement = (
            select(Camera)
            .where(Camera.junction_id == junction_id)
            .order_by(Camera.lane_id.asc())
        )

        return list(session.scalars(statement).all())

    def get_traffic_history(
        self,
        session: Session,
        limit: int = 50,
    ) -> list[TrafficAnalytics]:

        statement = (
            select(TrafficAnalytics)
            .order_by(TrafficAnalytics.timestamp.desc())
            .limit(limit)
        )

        return list(session.scalars(statement).all())

    def get_lane_history(
        self,
        session: Session,
        limit: int = 50,
    ) -> list[LaneAnalytics]:

        statement = (
            select(LaneAnalytics).order_by(LaneAnalytics.timestamp.desc()).limit(limit)
        )

        return list(session.scalars(statement).all())

    def get_signal_history(
        self,
        session: Session,
        limit: int = 50,
    ) -> list[SignalDecision]:

        statement = (
            select(SignalDecision)
            .order_by(SignalDecision.timestamp.desc())
            .limit(limit)
        )

        return list(session.scalars(statement).all())

    def _timestamp(self) -> datetime:
        return datetime.now(timezone.utc)

    def save_traffic_statistics(
        self,
        session: Session,
        statistics: TrafficStatistics,
    ) -> None:

        record = TrafficAnalytics(
            timestamp=self._timestamp(),
            current_vehicle_count=statistics.current_vehicle_count,
            total_vehicle_count=statistics.total_vehicle_count,
            average_speed=statistics.average_speed,
            density=statistics.density,
            queue_length=statistics.queue_length,
            waiting_vehicles=statistics.waiting_vehicles,
            average_waiting_time=statistics.average_waiting_time,
            maximum_waiting_time=statistics.maximum_waiting_time,
            pcu=statistics.pcu,
            traffic_flow=statistics.traffic_flow,
        )

        session.add(record)

    def save_lane_statistics(
        self,
        session: Session,
        statistics: list[LaneStatistics],
    ) -> None:

        timestamp = self._timestamp()

        for lane in statistics:

            record = LaneAnalytics(
                timestamp=timestamp,
                lane_id=lane.lane_id,
                vehicle_count=lane.vehicle_count,
                average_speed=lane.average_speed,
                density=lane.density,
                queue_length=lane.queue_length,
                traffic_flow=lane.traffic_flow,
            )

            session.add(record)

    def save_vehicle_event(
        self,
        session: Session,
        track: Track,
        event_type: str,
        speed: float | None = None,
    ) -> None:

        record = VehicleEvent(
            timestamp=self._timestamp(),
            track_id=track.track_id,
            vehicle_type=track.class_name,
            lane_id=track.lane_id,
            speed=speed,
            event_type=event_type,
        )

        session.add(record)

    def save_signal_decision(
        self,
        session: Session,
        decision: Decision,
    ) -> None:

        record = SignalDecision(
            timestamp=self._timestamp(),
            selected_lane=decision.selected_lane,
            green_time=decision.green_time,
            reason=decision.reason,
        )

        session.add(record)

    def save_camera(
        self,
        session: Session,
        name: str,
        source: str,
        source_type: str,
        location: str | None = None,
    ) -> Camera:

        camera = Camera(
            name=name,
            source=source,
            source_type=source_type,
            location=location,
            is_active=True,
            created_at=self._timestamp(),
        )

        session.add(camera)

        return camera
