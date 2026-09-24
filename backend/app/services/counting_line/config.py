from dataclasses import dataclass


@dataclass(slots=True)
class CountingLineConfig:

    start = (420, 560)

    end = (1500, 560)
