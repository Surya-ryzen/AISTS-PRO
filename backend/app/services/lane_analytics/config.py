from dataclasses import dataclass


@dataclass(slots=True)
class LaneAnalyticsConfig:
    """
    Configuration for lane analytics.
    """

    density_scale: float = 20.0
