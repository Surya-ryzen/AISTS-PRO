from dataclasses import dataclass


@dataclass(slots=True)
class StopLineConfig:

    start = (420, 640)

    end = (1500, 640)
