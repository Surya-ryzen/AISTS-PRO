from dataclasses import dataclass


@dataclass(slots=True)
class CameraConfig:

    default_width: int = 1920

    default_height: int = 1080

    default_fps: float = 30.0
