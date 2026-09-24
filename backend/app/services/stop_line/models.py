from dataclasses import dataclass


@dataclass(slots=True)
class StopLine:

    start: tuple[int, int]

    end: tuple[int, int]
