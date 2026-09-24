from backend.app.shared.model_registry import ModelRegistry

from .config import DetectionConfig
from .inference import DetectionInference


class DetectionService:

    def __init__(self):

        self.config = DetectionConfig()

        model = ModelRegistry.get_yolo(
            self.config.model
        )

        self.inference = DetectionInference(
            model,
            self.config
        )

    def detect(self, image):

        return self.inference.predict(image)