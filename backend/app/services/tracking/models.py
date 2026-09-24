from dataclasses import dataclass


@dataclass
class Track:

    track_id: int

    class_id: int

    class_name: str

    confidence: float

    x1: int
    y1: int
    x2: int
    y2: int

    lane_id: int | None = None
