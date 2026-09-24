from backend.app.services.analytics.calculators.base_calculator import BaseCalculator


class AverageSpeedCalculator(BaseCalculator):

    NAME = "Average Speed"

    def calculate(self, frame, tracks, speeds, statistics):

        if not speeds:
            statistics.average_speed = 0.0
            return statistics

        total_speed = sum(speed.speed_kmh for speed in speeds)

        statistics.average_speed = total_speed / len(speeds)

        return statistics
