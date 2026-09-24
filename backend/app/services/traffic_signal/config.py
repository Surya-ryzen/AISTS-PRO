from dataclasses import dataclass


@dataclass(slots=True)
class TrafficSignalConfig:
    """
    Configuration for the Traffic Signal.
    """

    lane_count: int = 3

    default_green_time: int = 30

    yellow_time: int = 5

    minimum_green_time: int = 10

    maximum_green_time: int = 60
