from backend.app.services.video_ingestion.service import VideoService
from backend.app.services.tracking.service import TrackingService

from backend.app.services.speed.config import SpeedConfig
from backend.app.services.speed.optical_flow import OpticalFlow
from backend.app.services.speed.service import SpeedService

from backend.app.services.analytics.service import AnalyticsService
from backend.app.services.lane.service import LaneService
from backend.app.services.lane_analytics.service import LaneAnalyticsService

from backend.app.services.roi.service import ROIService
from backend.app.services.stop_line.service import StopLineService
from backend.app.services.counting_line.service import CountingLineService
from backend.app.services.behavior.service import BehaviorService
from backend.app.services.incident_detection.service import IncidentDetectionService

from backend.app.services.traffic_signal.service import TrafficSignalService
from backend.app.services.decision_engine.service import DecisionEngineService
from .models import FrameResult
from .drawing import SystemDrawer
import threading
import time

from backend.app.database.session_manager import get_db_session
from backend.app.services.persistence.service import PersistenceService
from backend.app.services.video_ingestion.exceptions import VideoEndOfStream


class TrafficSystemService:
    """
    Central orchestrator for the entire traffic analytics system.
    """

    def __init__(self):

        # -----------------------------
        # Video
        # -----------------------------
        self.video = None

        # -----------------------------
        # Tracking
        # -----------------------------
        self.tracker = TrackingService()

        # -----------------------------
        # Speed
        # -----------------------------
        speed_config = SpeedConfig()

        self.optical_flow = OpticalFlow(speed_config.optical_flow)

        self.speed = SpeedService(speed_config)

        # -----------------------------
        # Analytics
        # -----------------------------
        self.analytics = AnalyticsService()

        self.lane_analytics = LaneAnalyticsService()

        # -----------------------------
        # Spatial
        # -----------------------------
        self.lane = LaneService()

        self.roi = ROIService()

        self.stop_line = StopLineService()

        self.counting_line = CountingLineService()

        self.behavior = BehaviorService(
            stop_line_y=self.stop_line.stop_line.start[1],
            counting_line_y=self.counting_line.counting_line.start[1],
        )

        self.incident_detection = IncidentDetectionService()

        # -----------------------------
        # AI
        # -----------------------------
        self.signal = TrafficSignalService()

        self.decision = DecisionEngineService()
        self.drawer = SystemDrawer()
        self.persistence = PersistenceService()

        from backend.app.services.prediction.collection import ForecastCollector
        self.forecast_collector = ForecastCollector()
        self.last_persistence_time = 0.0
        self.persistence_interval = 10.0
        # -----------------------------
        # Background Processing
        # -----------------------------

        self.running = False
        self.thread = None
        self.latest_result = None
        self.latest_image = None

    # -----------------------------
    # Public API
    # -----------------------------

    def start(self):
        """
        Start background processing.
        """

        camera_source = None

        try:
            with get_db_session() as session:

                camera = self.persistence.get_active_camera(session)

                if camera is not None:
                    camera_source = camera.source

                    print(f"Using active camera: " f"{camera.name}")

        except Exception:

            import traceback

            print(
                "Unable to load camera from database. "
                "Falling back to YAML configuration."
            )

            traceback.print_exc()

        self.video = VideoService(source=camera_source)

        self.video.start()
        self.roi.reset(self.video.reader.config.source)
        self.pending_roi = None

        from backend.app.services.anpr.live import LiveEmergencyRecorder
        self.emergency_recorder = LiveEmergencyRecorder()
        self.running = True

        self.thread = threading.Thread(
            target=self._processing_loop,
            daemon=True,
        )

        self.thread.start()

    def stop(self):
        """
        Stop background processing.
        """

        self.running = False

        if self.thread is not None:
            self.thread.join()

        if self.video is not None:
            self.video.stop()

    def process_frame(self):
        """
        Process one complete frame through the AI pipeline.
        """

        frame = self.video.get_frame()

        image = frame.image.copy()
        if getattr(self, '_emergency_loop', None) != frame.loop_index:
            from backend.app.services.anpr.live import LiveEmergencyRecorder
            self.emergency_recorder = LiveEmergencyRecorder()
            self._emergency_loop = frame.loop_index

        # -----------------------------
        # Tracking
        # -----------------------------
        if getattr(self, "pending_roi", None) is not None:
            self.roi.reset(self.video.reader.config.source)
            self.analytics = AnalyticsService()
            self.behavior.vehicle_states.clear()
            from backend.app.services.anpr.live import LiveEmergencyRecorder
            self.emergency_recorder = LiveEmergencyRecorder()
            self.pending_roi = None
        raw_tracks = self.tracker.track(image)
        tracks = self.roi.update(image, raw_tracks)
        line = self.roi.counting_line()
        if line:
            (
                self.counting_line.counting_line.start,
                self.counting_line.counting_line.end,
            ) = line
            self.behavior.counting_line_y = line[0][1]
        # A physical stop line cannot be inferred from vehicle movement.
        self.behavior.stop_line_y = -1

        for track in tracks:
            self.roi.assign_lane(track)

        # -----------------------------
        # Optical Flow
        # -----------------------------

        self.emergency_recorder.process(image, tracks, frame.frame_id,
            self.video.reader.config.source, bool(self.roi.manual_lanes))

        flow = self.optical_flow.compute(image)
        # -----------------------------
        # Speed
        # -----------------------------

        speeds = self.speed.calculate(
            flow,
            tracks,
        )

        # -----------------------------
        # Analytics
        # -----------------------------
        statistics = self.analytics.process(
            frame,
            tracks,
            speeds,
        )

        lane_statistics = self.lane_analytics.process(
            tracks,
            speeds,
        )

        # -----------------------------
        # Behavior
        # -----------------------------
        from backend.app.services.lane_analytics.models import LaneStatistics

        present = {lane.lane_id for lane in lane_statistics}
        lane_statistics.extend(
            LaneStatistics(lane_id=i)
            for i in range(1, self.roi.lane_count + 1)
            if i not in present
        )
        lane_statistics.sort(key=lambda lane: lane.lane_id)
        self.forecast_collector.process(frame, lane_statistics, self.video.reader.config.source, self.roi.profile)
        behavior_events = {}

        for track in tracks:

            behavior_events[track.track_id] = self.behavior.update(track)

        # -----------------------------
        # Incident Detection
        # -----------------------------

        incidents = self.incident_detection.process(
            tracks=tracks,
            speeds=speeds,
            behavior_events=behavior_events,
        )

        # -----------------------------
        # Decision Engine
        # -----------------------------

        needs_decision = self.signal.update()

        if needs_decision and self.roi.ready:

            from backend.app.services.anpr.priority import choose_priority
            with get_db_session() as session:
                decision = choose_priority(session,self.video.reader.config.source,
                    self.emergency_recorder.run_id,len(self.roi.manual_lanes))
            if decision is None:
                decision = self.decision.process(lane_statistics,self.signal.get_state().current_green_lane)

            self.decision.last_decision = decision
            self.signal.apply_decision(decision)

            with get_db_session() as session:

                self.persistence.save_signal_decision(
                    session,
                    decision,
                )
        if self.roi.ready:
            self._persist_result(statistics, lane_statistics)
        result = FrameResult(
            frame=frame,
            image=image,
            tracks=tracks,
            speeds=speeds,
            statistics=statistics,
            lane_statistics=lane_statistics,
            behavior_events=behavior_events,
            signal=self.signal.get_state(),
            incidents=incidents,
        )

        image = self.drawer.draw(
            image,
            result,
            self,
        )

        result.image = image
        self.latest_result = result
        self.latest_image = image.copy()
        return result

    def _persist_result(self, statistics, lane_statistics):
        """
        Persist periodic traffic analytics and lane analytics.
        """

        current_time = time.monotonic()

        if current_time - self.last_persistence_time < self.persistence_interval:
            return

        with get_db_session() as session:

            self.persistence.save_traffic_statistics(
                session,
                statistics,
            )

            self.persistence.save_lane_statistics(
                session,
                lane_statistics,
            )

        self.last_persistence_time = current_time

    def _processing_loop(self):

        while self.running:

            try:

                self.process_frame()

            except VideoEndOfStream:

                print("Video stream ended.")

                self.running = False
                break

            except Exception:

                import traceback

                traceback.print_exc()

                self.running = False
                break

            time.sleep(0.001)

    def get_latest_result(self):
        """
        Returns the latest processed frame.
        """

        return self.latest_result

    def get_latest_image(self):
        """
        Returns the latest processed image.
        """

        return self.latest_image
