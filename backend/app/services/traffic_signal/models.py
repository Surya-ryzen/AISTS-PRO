from dataclasses import dataclass
from enum import Enum


class SignalState(Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


@dataclass(slots=True)
class TrafficSignal:
    """
    Represents the current state of the traffic signal.
    """

    current_green_lane: int = 1

    state: SignalState = SignalState.GREEN

    green_time: int = 30

    yellow_time: int = 5

    red_time: int = 30

    remaining_time: int = 30

    # Last AI Decision
    last_reason: str = "System Started"
