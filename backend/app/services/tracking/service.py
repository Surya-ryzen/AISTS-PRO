from backend.app.services.detection.config import DetectionConfig
from backend.app.shared.model_registry import ModelRegistry

from .config import TrackingConfig
from .models import Track


class TrackingService:

    def __init__(self):

        self.config = TrackingConfig()

        # Use the same model and vehicle classes
        # as the detection configuration.
        detection_config = DetectionConfig()

        self.model = ModelRegistry.get_yolo(detection_config.model)

        self.vehicle_classes = detection_config.vehicle_classes

    def track(self, image):

        results = self.model.track(
            image,
            persist=self.config.persist,
            tracker=self.config.tracker,
            conf=self.config.confidence,
            iou=self.config.iou,
            verbose=False,
        )

        tracks = []

        result = results[0]

        if result.boxes.id is None:
            return tracks

        for box, track_id in zip(
            result.boxes,
            result.boxes.id,
        ):

            class_id = int(box.cls[0])

            class_name = self.model.names[class_id]

            if class_name not in self.vehicle_classes:
                continue

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0],
            )

            confidence = float(box.conf[0])

            tracks.append(
                Track(
                    track_id=int(track_id),
                    class_id=class_id,
                    class_name=class_name,
                    confidence=confidence,
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                )
            )

        return tracks
