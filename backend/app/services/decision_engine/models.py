from dataclasses import dataclass


@dataclass(slots=True)
class Decision:
    """
    Represents the AI's decision.
    """

    selected_lane: int

    green_time: int

    reason: str
