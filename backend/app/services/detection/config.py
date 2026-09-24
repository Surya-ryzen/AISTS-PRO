from pathlib import Path
import yaml

CONFIG_FILE = Path("configs/detection.yaml")


class DetectionConfig:

    def __init__(self):

        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)["detection"]

        self.model = config["model"]
        self.confidence = config["confidence_threshold"]
        self.iou = config["iou_threshold"]
        self.device = config["device"]
        self.vehicle_classes = config["vehicle_classes"]
        self.img_size = config["img_size"]
