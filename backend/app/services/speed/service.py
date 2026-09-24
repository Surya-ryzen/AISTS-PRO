from backend.app.services.speed.motion_extractor import MotionExtractor
from backend.app.services.speed.speed_estimator import SpeedEstimator
from backend.app.services.speed.models import VehicleSpeed

import time


class SpeedService:

    def __init__(self, config):

        self.estimator = SpeedEstimator(config)

    def calculate(self, flow, tracks):

        results = []

        for track in tracks:

            motion = MotionExtractor.extract(flow, track)

            if motion is None:
                continue

            dx, dy = motion

            pixel_distance, speed = self.estimator.estimate(dx, dy)

            results.append(
                VehicleSpeed(
                    track_id=track.track_id,
                    class_name=track.class_name,
                    speed_kmh=speed,
                    pixel_distance=pixel_distance,
                    timestamp=time.time()
                )
            )

        return results