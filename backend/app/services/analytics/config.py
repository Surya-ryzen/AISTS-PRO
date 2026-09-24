from backend.app.shared.config_manager import ConfigManager


class AnalyticsConfig:

    def __init__(self):

        config = ConfigManager.get("analytics")["analytics"]

        self.density = config["density"]

        self.queue = config["queue"]

        self.waiting = config["waiting"]

        self.pcu = config["pcu"]