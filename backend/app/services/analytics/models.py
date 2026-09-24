from dataclasses import dataclass


@dataclass(slots=True)
class TrafficStatistics:
    """
    Stores all traffic analytics computed for the current frame.
    """

    # -----------------------------
    # Vehicle Counts
    # -----------------------------
    current_vehicle_count: int = 0
    total_vehicle_count: int = 0

    # -----------------------------
    # Speed
    # -----------------------------
    average_speed: float = 0.0

    # -----------------------------
    # Congestion
    # -----------------------------
    density: float = 0.0
    queue_length: int = 0

    # -----------------------------
    # Waiting Time
    # -----------------------------
    waiting_vehicles: int = 0
    average_waiting_time: float = 0.0
    maximum_waiting_time: float = 0.0

    # -----------------------------
    # Traffic Metrics
    # -----------------------------
    pcu: float = 0.0
    traffic_flow: float = 0.0
    vehicles_passed_last_minute: int = 0
