from backend.app.services.detection.models import Detection


class DetectionInference:

    def __init__(self, model, config):
        self.model = model
        self.config = config

    def predict(self, image):

        results = self.model(
            image,
            conf=self.config.confidence,
            iou=self.config.iou,
            device=self.config.device,
            imgsz=self.config.img_size,
            verbose=False,
        )

        detections = []

        result = results[0]

        for box in result.boxes:

            class_id = int(box.cls[0])

            class_name = self.model.names[class_id]

            if class_name not in self.config.vehicle_classes:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            confidence = float(box.conf[0])

            detections.append(
                Detection(
                    class_id=class_id,
                    class_name=class_name,
                    confidence=confidence,
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                )
            )

        return detections
