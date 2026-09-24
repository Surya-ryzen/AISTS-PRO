from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass(slots=True)
class Frame:
    """
    Represents one frame received from a video source.
    """

    frame_id: int

    image: np.ndarray

    timestamp: float

    source_seconds: float | None = None
    loop_index: int = 0


@dataclass(slots=True)
class VideoInfo:
    """
    Metadata about the opened video source.
    """

    width: int

    height: int

    fps: float

    total_frames: Optional[int]

    source: str