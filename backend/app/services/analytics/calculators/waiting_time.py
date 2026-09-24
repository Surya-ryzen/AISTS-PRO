from backend.app.services.analytics.calculators.base_calculator import (
    BaseCalculator,
)

from backend.app.services.analytics.config import AnalyticsConfig


class WaitingTimeCalculator(BaseCalculator):

    NAME = "Waiting Time"

    def __init__(self):

        self.config = AnalyticsConfig()

        # Stores waiting information for each vehicle
        # {
        #     track_id: {
        #         "waiting_time": float,
        #         "last_timestamp": float
        #     }
        # }
        self.waiting_data = {}

    def calculate(
        self,
        frame,
        tracks,
        speeds,
        statistics,
    ):
        """
        Updates waiting time statistics using frame timestamps.
        """

        threshold = self.config.waiting["speed_threshold"]

        current_timestamp = frame.timestamp

        active_track_ids = set()

        for vehicle in speeds:

            track_id = vehicle.track_id

            active_track_ids.add(track_id)

            # First time seeing this vehicle
            if track_id not in self.waiting_data:

                self.waiting_data[track_id] = {
                    "waiting_time": 0.0,
                    "last_timestamp": current_timestamp,
                }

            data = self.waiting_data[track_id]

            elapsed = current_timestamp - data["last_timestamp"]

            # Update timestamp
            data["last_timestamp"] = current_timestamp

            if vehicle.speed_kmh <= threshold:

                data["waiting_time"] += elapsed

            else:

                data["waiting_time"] = 0.0

        # Remove vehicles that disappeared
        for track_id in list(self.waiting_data.keys()):

            if track_id not in active_track_ids:

                del self.waiting_data[track_id]

        # Collect waiting times
        waiting_times = [
            data["waiting_time"]
            for data in self.waiting_data.values()
            if data["waiting_time"] > 0
        ]

        statistics.waiting_vehicles = len(waiting_times)

        if waiting_times:

            statistics.average_waiting_time = sum(waiting_times) / len(waiting_times)

            statistics.maximum_waiting_time = max(waiting_times)

        else:

            statistics.average_waiting_time = 0.0
            statistics.maximum_waiting_time = 0.0

        return statistics
