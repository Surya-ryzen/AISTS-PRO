from dataclasses import dataclass
import time


@dataclass(slots=True)
class VehicleState:
    """
    Stores the previous state of a tracked vehicle.
    """

    track_id: int

    previous_center: tuple[int, int]

    crossed_stop_line: bool = False
    crossed_counting_line: bool = False

    waiting: bool = False

    waiting_start_time: float = 0.0

    last_seen_time: float = time.time()
