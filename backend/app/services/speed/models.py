from dataclasses import dataclass


@dataclass
class VehicleSpeed:
    """
    Represents the estimated speed of a tracked vehicle.
    """

    track_id: int

    class_name: str

    speed_kmh: float

    pixel_distance: float

    timestamp: float