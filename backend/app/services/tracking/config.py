from pathlib import Path
import yaml


CONFIG_FILE = Path("configs/tracking.yaml")


class TrackingConfig:

    def __init__(self):

        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)["tracking"]

        self.tracker = config["tracker"]
        self.persist = config["persist"]
        self.confidence = config["confidence_threshold"]
        self.iou = config["iou_threshold"]
        self.display_track_id = config["display_track_id"]