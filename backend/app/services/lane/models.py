from dataclasses import dataclass


@dataclass(slots=True)
class Lane:

    lane_id: int

    name: str

    left_boundary: int

    right_boundary: int
