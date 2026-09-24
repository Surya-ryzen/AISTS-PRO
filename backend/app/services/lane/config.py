from dataclasses import dataclass


@dataclass(slots=True)
class LaneConfig:

    frame_width: int = 1920

    lane_count: int = 3
