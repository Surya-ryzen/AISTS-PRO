import cv2

from .config import StopLineConfig
from .models import StopLine


class StopLineService:

    def __init__(self):

        config = StopLineConfig()

        self.stop_line = StopLine(
            start=config.start,
            end=config.end,
        )

    def draw(self, image):

        cv2.line(
            image,
            self.stop_line.start,
            self.stop_line.end,
            (0, 0, 255),
            3,
        )

        return image
