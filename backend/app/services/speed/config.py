from backend.app.shared.config_manager import ConfigManager


class SpeedConfig:

    def __init__(self):

        config = ConfigManager.get("speed")["speed"]

        self.fps = config["fps"]
        self.pixel_to_meter = config["pixel_to_meter"]
        self.smoothing_window = config["smoothing_window"]

        self.optical_flow = config["optical_flow"]