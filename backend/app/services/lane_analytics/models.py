from dataclasses import dataclass


@dataclass(slots=True)
class LaneStatistics:
    """
    Stores analytics for a single lane.
    """

    lane_id: int

    vehicle_count: int = 0

    average_speed: float = 0.0

    density: float = 0.0

    queue_length: int = 0

    traffic_flow: float = 0.0
