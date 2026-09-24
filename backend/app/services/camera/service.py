from .config import CameraConfig
from .models import Camera


class CameraService:

    def __init__(self):

        self.config = CameraConfig()

    def create_camera(
        self,
        camera_id: int,
        name: str,
        location: str,
        junction: str,
    ) -> Camera:

        return Camera(
            camera_id=camera_id,
            name=name,
            location=location,
            junction=junction,
            width=self.config.default_width,
            height=self.config.default_height,
            fps=self.config.default_fps,
        )
