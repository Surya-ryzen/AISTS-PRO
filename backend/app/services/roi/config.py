from dataclasses import dataclass


@dataclass(slots=True)
class ROIConfig:

    polygon = [
        (250, 1080),
        (700, 300),
        (1220, 300),
        (1670, 1080),
    ]
