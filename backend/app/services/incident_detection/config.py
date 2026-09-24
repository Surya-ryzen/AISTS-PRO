from backend.app.shared.config_manager import ConfigManager


class IncidentDetectionConfig:
    """
    Configuration for incident detection.
    """

    def __init__(self):
        config = ConfigManager.get("incident_detection")["incident_detection"]

        self.speed_violation_enabled = config["speed_violation"]["enabled"]
        self.speed_limit_kmh = config["speed_violation"]["speed_limit_kmh"]
        self.speed_tolerance_kmh = config["speed_violation"]["tolerance_kmh"]

        self.accident_enabled = config["accident"]["enabled"]
