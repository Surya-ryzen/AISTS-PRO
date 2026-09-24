from dataclasses import dataclass


@dataclass(slots=True)
class CountingLine:

    start: tuple[int, int]

    end: tuple[int, int]
