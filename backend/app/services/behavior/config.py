from dataclasses import dataclass


@dataclass(slots=True)
class BehaviorConfig:

    waiting_speed_threshold: float = 2.0

    waiting_time_threshold: float = 2.0
