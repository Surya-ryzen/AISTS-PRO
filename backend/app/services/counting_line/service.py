import cv2

from .config import CountingLineConfig
from .models import CountingLine


class CountingLineService:

    def __init__(self):

        config = CountingLineConfig()

        self.counting_line = CountingLine(
            start=config.start,
            end=config.end,
        )

    def draw(self, image):

        cv2.line(
            image,
            self.counting_line.start,
            self.counting_line.end,
            (0, 0, 255),
            3,
        )

        return image
