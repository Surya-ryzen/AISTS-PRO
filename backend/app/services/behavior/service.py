from .models import VehicleState


class BehaviorService:

    def __init__(
        self,
        stop_line_y: int,
        counting_line_y: int,
    ):

        self.stop_line_y = stop_line_y
        self.counting_line_y = counting_line_y

        self.vehicle_states = {}

    def update(self, track):

        center_x = (track.x1 + track.x2) // 2
        center_y = (track.y1 + track.y2) // 2

        center = (
            center_x,
            center_y,
        )

        events = {
            "stop_line_crossed": False,
            "counting_line_crossed": False,
        }

        # -----------------------------
        # New Vehicle
        # -----------------------------

        if track.track_id not in self.vehicle_states:

            self.vehicle_states[track.track_id] = VehicleState(
                track_id=track.track_id,
                previous_center=center,
            )

            return events

        state = self.vehicle_states[track.track_id]

        previous_y = state.previous_center[1]

        # -----------------------------
        # Stop Line Crossing
        # -----------------------------

        if (
            not state.crossed_stop_line
            and previous_y < self.stop_line_y
            and center_y >= self.stop_line_y
        ):

            state.crossed_stop_line = True
            events["stop_line_crossed"] = True

        # -----------------------------
        # Counting Line Crossing
        # -----------------------------

        if (
            not state.crossed_counting_line
            and (previous_y - self.counting_line_y) * (center_y - self.counting_line_y) <= 0
            and previous_y != center_y
        ):

            state.crossed_counting_line = True
            events["counting_line_crossed"] = True

        # -----------------------------
        # Update Memory
        # -----------------------------

        state.previous_center = center

        return events

