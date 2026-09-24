from ultralytics import YOLO

from .config import DetectionConfig
from .exceptions import ModelLoadError


class ModelLoader:

    def __init__(self):

        self.config = DetectionConfig()
        self.model = None

    def load(self):

        try:

            self.model = YOLO(self.config.model)

            return self.model

        except Exception as e:

            raise ModelLoadError(
                f"Unable to load model: {e}"
            )