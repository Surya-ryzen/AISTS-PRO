from dataclasses import dataclass


@dataclass(slots=True)
class Camera:

    camera_id: int

    name: str

    location: str

    junction: str

    width: int

    height: int

    fps: float

    active: bool = True
