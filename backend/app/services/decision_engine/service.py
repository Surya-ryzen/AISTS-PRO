from .config import DecisionConfig
from .models import Decision


class DecisionEngineService:
    """
    Rule-based adaptive traffic signal decision engine.
    """

    def __init__(self):

        self.config = DecisionConfig()
        self.last_decision = None

    def process(
        self,
        lane_statistics,
        current_green_lane,
    ) -> Decision:

        if not lane_statistics:

            return Decision(
                selected_lane=current_green_lane,
                green_time=self.config.low_green_time,
                reason="No lane statistics available",
            )

        # ------------------------------------
        # Select Best Lane
        # ------------------------------------

        best_lane = max(
            lane_statistics,
            key=lambda lane: (
                lane.queue_length,
                lane.vehicle_count,
            ),
        )

        # ------------------------------------
        # Avoid unnecessary switching
        # ------------------------------------

        current_lane = next(
            (lane for lane in lane_statistics if lane.lane_id == current_green_lane),
            None,
        )

        if current_lane is not None:

            if (
                current_lane.queue_length == best_lane.queue_length
                and current_lane.vehicle_count == best_lane.vehicle_count
            ):

                best_lane = current_lane

        # ------------------------------------
        # Decide Green Time
        # ------------------------------------

        queue = best_lane.queue_length

        if queue <= self.config.low_queue_threshold:

            green_time = self.config.low_green_time

            reason = "Low Queue"

        elif queue <= self.config.medium_queue_threshold:

            green_time = self.config.medium_green_time

            reason = "Medium Queue"

        else:

            green_time = self.config.high_green_time

            reason = "High Queue"

        decision = Decision(
            selected_lane=best_lane.lane_id,
            green_time=green_time,
            reason=reason,
        )

        self.last_decision = decision

        return decision
