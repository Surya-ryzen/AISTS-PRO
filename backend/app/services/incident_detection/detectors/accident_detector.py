from dataclasses import dataclass
import math
import time

from backend.app.services import speed


@dataclass
class VehicleMotionState:
    """
    Stores recent motion information for a tracked vehicle.
    """

    track_id: int
    previous_center: tuple[int, int]
    previous_speed: float
    previous_timestamp: float
    stationary_since: float | None = None


class AccidentDetector:
    """
    Detects suspected vehicle collisions using vehicle proximity,
    speed changes, and motion history.
    """

    def __init__(self):
        self.vehicle_states: dict[int, VehicleMotionState] = {}

    @staticmethod
    def _get_center(track) -> tuple[int, int]:
        return (
            (track.x1 + track.x2) // 2,
            (track.y1 + track.y2) // 2,
        )

    @staticmethod
    def _distance(
        point_a: tuple[int, int],
        point_b: tuple[int, int],
    ) -> float:

        return math.sqrt(
            (point_a[0] - point_b[0]) ** 2 + (point_a[1] - point_b[1]) ** 2
        )

    def detect(
        self,
        tracks,
        speeds,
        behavior_events,
    ) -> list:

        current_time = time.time()

        speed_by_track = {speed.track_id: speed for speed in speeds}

        current_states = {}

        # ---------------------------------
        # Update vehicle motion history
        # ---------------------------------

        for track in tracks:

            center = self._get_center(track)

            speed_data = speed_by_track.get(track.track_id)

            speed = speed_data.speed_kmh if speed_data is not None else 0.0

            previous_state = self.vehicle_states.get(track.track_id)
            speed_drop = 0.0

            if previous_state is not None:
                speed_drop = self._calculate_speed_drop(
                    previous_state.previous_speed,
                    speed,
                )

            if previous_state is None:

                current_states[track.track_id] = VehicleMotionState(
                    track_id=track.track_id,
                    previous_center=center,
                    previous_speed=speed,
                    previous_timestamp=current_time,
                )

                continue

            current_states[track.track_id] = VehicleMotionState(
                track_id=track.track_id,
                previous_center=center,
                previous_speed=speed,
                previous_timestamp=current_time,
            )

        self.vehicle_states = current_states

        # Accident detection will be added next.
        return []

    def _calculate_speed_drop(
        self,
        previous_speed: float,
        current_speed: float,
    ) -> float:
        """
        Calculates the reduction in vehicle speed between frames.
        """

        return max(
            0.0,
            previous_speed - current_speed,
        )
