import time

from .config import TrafficSignalConfig
from .models import TrafficSignal, SignalState


class TrafficSignalService:
    """
    Controls the traffic signal.
    """

    def __init__(self):

        self.config = TrafficSignalConfig()

        self.signal = TrafficSignal(
            current_green_lane=1,
            state=SignalState.GREEN,
            green_time=self.config.default_green_time,
            yellow_time=self.config.yellow_time,
            red_time=self.config.default_green_time,
            remaining_time=self.config.default_green_time,
        )

        self.last_update = time.monotonic()

    # ----------------------------------
    # Public API
    # ----------------------------------

    def update(self):
        """
        Update the traffic signal timer.

        Returns:
            bool: True if a new AI decision is required.
        """

        now = time.monotonic()
        elapsed = now-self.last_update
        if elapsed < 1:
            return False
        elapsed = int(elapsed)
        self.last_update += elapsed
        self.signal.remaining_time = max(0, self.signal.remaining_time-elapsed)
        if self.signal.remaining_time > 0:
            return False
        if self.signal.state == SignalState.GREEN:
            self.signal.state = SignalState.YELLOW
            self.signal.remaining_time = self.config.yellow_time
            return False
        if self.signal.state == SignalState.YELLOW:
            self.signal.state = SignalState.RED
            self.signal.remaining_time = 2
            return False
        return True

    def get_state(self):

        return self.signal

    def apply_decision(self, decision):
        """
        Apply a new decision from the AI.
        """

        self.last_update = time.monotonic()
        self.signal.current_green_lane = decision.selected_lane

        self.signal.green_time = decision.green_time

        self.signal.remaining_time = decision.green_time

        self.signal.state = SignalState.GREEN

        self.signal.last_reason = decision.reason
