import math


class SpeedEstimator:
    """
    Converts motion vectors into speed estimates.
    """

    def __init__(self, config):

        self.config = config

    def estimate(self, dx, dy):

        pixel_distance = math.sqrt(dx ** 2 + dy ** 2)

        meters = pixel_distance * self.config.pixel_to_meter

        speed_mps = meters * self.config.fps

        speed_kmh = speed_mps * 3.6

        return pixel_distance, speed_kmh