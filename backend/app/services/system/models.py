from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class FrameResult:
    """
    Contains all outputs produced while processing one video frame.
    """

    frame: Any

    image: Any

    tracks: list

    speeds: list

    statistics: Any

    lane_statistics: list

    behavior_events: dict

    signal: Any

    incidents: list
