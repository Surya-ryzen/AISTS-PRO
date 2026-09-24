from dataclasses import dataclass


@dataclass(slots=True)
class DecisionConfig:

    low_queue_threshold: int = 2

    medium_queue_threshold: int = 5

    low_green_time: int = 15

    medium_green_time: int = 25

    high_green_time: int = 40
