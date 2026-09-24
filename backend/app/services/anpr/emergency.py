"""Optional custom emergency detector. Standard COCO YOLO has no ambulance class."""
import os
import threading
from pathlib import Path


class EmergencyDetector:
    def __init__(self):
        self.model = None
        self.lock = threading.Lock()

    def detect(self, image):
        from backend.app.core.settings import settings
        path = os.getenv('WEEK10_EMERGENCY_MODEL', settings.WEEK10_EMERGENCY_MODEL)
        if not path:
            return []
        if not Path(path).is_file():
            raise RuntimeError('WEEK10_EMERGENCY_MODEL does not point to a local weight file.')
        with self.lock:
            if self.model is None:
                from ultralytics import YOLO
                self.model = YOLO(path)
            result = self.model.predict(image, conf=.5, verbose=False)[0]
            aliases = {'ambulance':'ambulance','fire truck':'fire_engine','fire engine':'fire_engine',
                       'firetruck':'fire_engine','fire engine truck':'fire_engine','police car':'police'}
            configured = {str(name).lower().replace('_',' ') for name in self.model.names.values()}
            if not configured.intersection(aliases):
                raise RuntimeError('Configured weights lack supported emergency classes. Do not use COCO yolov8s.pt.')
            candidates = []
            for box in result.boxes:
                name = str(result.names[int(box.cls[0])]).lower().replace('_',' ')
                if name in aliases:
                    candidates.append(dict(vehicle_type=aliases[name], confidence=float(box.conf[0]),
                        evidence='Custom detector: '+name+'; box='+str([int(v) for v in box.xyxy[0]]),
                        method='custom_detector', bbox=[float(v) for v in box.xyxy[0]]))
            return candidates


detector = EmergencyDetector()
