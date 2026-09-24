from dataclasses import dataclass


@dataclass(slots=True)
class ROI:

    points: list[tuple[int, int]]
