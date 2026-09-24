from .config import LaneConfig
from .models import Lane


class LaneService:

    def __init__(self):

        self.config = LaneConfig()

        lane_width = self.config.frame_width // self.config.lane_count

        self.lanes = []

        for i in range(self.config.lane_count):

            self.lanes.append(
                Lane(
                    lane_id=i + 1,
                    name=f"Lane {i + 1}",
                    left_boundary=i * lane_width,
                    right_boundary=(i + 1) * lane_width,
                )
            )

    def get_lane(self, center_x: int) -> Lane | None:

        for lane in self.lanes:

            if lane.left_boundary <= center_x < lane.right_boundary:

                return lane

        return None

    def assign_lane(self, track):

        center_x = (track.x1 + track.x2) // 2

        lane = self.get_lane(center_x)

        if lane:

            track.lane_id = lane.lane_id

        return track
