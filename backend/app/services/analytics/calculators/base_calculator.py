from abc import ABC, abstractmethod


class BaseCalculator(ABC):
    """
    Base class for all analytics calculators.
    """

    NAME = "Base Calculator"

    @abstractmethod
    def calculate(self, tracks, speeds, statistics):
        """
        Updates the shared TrafficStatistics object.
        """
        pass