from backend.app.services.analytics.calculators.base_calculator import BaseCalculator
from backend.app.services.analytics.config import AnalyticsConfig


class QueueLengthCalculator(BaseCalculator):
    """
    Calculates the number of vehicles
    that are considered to be in a queue.
    """

    NAME = "Queue Length"

    def __init__(self):

        self.config = AnalyticsConfig()

    def calculate(
        self,
        frame,
        tracks,
        speeds,
        statistics,
    ):

        threshold = self.config.queue["speed_threshold"]

        queue_length = 0

        for vehicle in speeds:

            if vehicle.speed_kmh <= threshold:

                queue_length += 1

        statistics.queue_length = queue_length

        return statistics
