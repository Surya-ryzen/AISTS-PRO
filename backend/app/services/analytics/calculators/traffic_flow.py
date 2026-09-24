from collections import deque

from backend.app.services.analytics.calculators.base_calculator import (
    BaseCalculator,
)


class TrafficFlowCalculator(BaseCalculator):

    NAME = "Traffic Flow"

    WINDOW_SECONDS = 60.0

    def __init__(self):

        # (timestamp, track_id)
        self.vehicle_history = deque()

        # Prevent duplicate counting
        self.active_track_ids = set()

    def calculate(
        self,
        frame,
        tracks,
        speeds,
        statistics,
    ):

        current_time = frame.timestamp

        # ---------------------------------
        # Add newly seen vehicles
        # ---------------------------------

        for track in tracks:

            if track.track_id not in self.active_track_ids:

                self.active_track_ids.add(track.track_id)

                self.vehicle_history.append(
                    (
                        current_time,
                        track.track_id,
                    )
                )

        # ---------------------------------
        # Remove vehicles older than 60 sec
        # ---------------------------------

        while self.vehicle_history:

            timestamp, track_id = self.vehicle_history[0]

            if current_time - timestamp <= self.WINDOW_SECONDS:

                break

            self.vehicle_history.popleft()

            self.active_track_ids.discard(track_id)

        # ---------------------------------
        # Statistics
        # ---------------------------------

        vehicles = len(self.vehicle_history)

        statistics.vehicles_passed_last_minute = vehicles

        statistics.traffic_flow = vehicles * 60

        return statistics
