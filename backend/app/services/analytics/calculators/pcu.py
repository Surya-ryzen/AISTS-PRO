from backend.app.services.analytics.calculators.base_calculator import (
    BaseCalculator,
)

from backend.app.services.analytics.config import AnalyticsConfig


class PCUCalculator(BaseCalculator):

    NAME = "Passenger Car Unit"

    def __init__(self):

        self.config = AnalyticsConfig()

    def calculate(
        self,
        frame,
        tracks,
        speeds,
        statistics,
    ):
        """
        Calculates the total Passenger Car Unit (PCU)
        for all currently tracked vehicles.
        """

        pcu_weights = self.config.pcu

        total_pcu = 0.0

        for track in tracks:

            vehicle = track.class_name.lower()

            total_pcu += pcu_weights.get(vehicle, 1.0)

        statistics.pcu = total_pcu

        return statistics
