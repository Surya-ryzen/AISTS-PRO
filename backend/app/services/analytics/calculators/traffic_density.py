from backend.app.services.analytics.calculators.base_calculator import (
    BaseCalculator,
)

from backend.app.services.analytics.config import AnalyticsConfig


class TrafficDensityCalculator(BaseCalculator):

    NAME = "Traffic Density"

    def __init__(self):

        self.config = AnalyticsConfig()

    def calculate(
        self,
        frame,
        tracks,
        speeds,
        statistics,
    ):

        max_vehicles = self.config.density["max_vehicles"]

        density = statistics.current_vehicle_count / max_vehicles

        statistics.density = min(
            density,
            1.0,
        )

        return statistics
