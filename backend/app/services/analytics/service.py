from backend.app.services.analytics.models import TrafficStatistics
from backend.app.services.analytics.pipeline import PIPELINE


class AnalyticsService:
    """
    Executes the analytics pipeline.
    """

    def __init__(self):

        self.calculators = [type(calculator)() for calculator in PIPELINE]

    def process(self, frame, tracks, speeds):

        statistics = TrafficStatistics()

        for calculator in self.calculators:

            calculator.calculate(
                frame,
                tracks,
                speeds,
                statistics,
            )

        return statistics

