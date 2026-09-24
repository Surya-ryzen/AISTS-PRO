from collections import defaultdict

from .models import LaneStatistics


class LaneAnalyticsService:
    """
    Computes lane-wise traffic analytics.
    """

    def process(self, tracks, speeds):

        # -----------------------------
        # Speed Lookup
        # -----------------------------

        speed_lookup = {speed.track_id: speed.speed_kmh for speed in speeds}

        # -----------------------------
        # Group Tracks by Lane
        # -----------------------------

        lane_tracks = defaultdict(list)

        for track in tracks:

            if track.lane_id is None:
                continue

            lane_tracks[track.lane_id].append(track)

        # -----------------------------
        # Compute Statistics
        # -----------------------------

        statistics = []

        for lane_id in sorted(lane_tracks):

            tracks_in_lane = lane_tracks[lane_id]

            vehicle_count = len(tracks_in_lane)

            speeds_in_lane = []

            queue_length = 0

            for track in tracks_in_lane:

                speed = speed_lookup.get(
                    track.track_id,
                    0.0,
                )

                speeds_in_lane.append(speed)

                if speed < 2.0:
                    queue_length += 1

            average_speed = (
                sum(speeds_in_lane) / len(speeds_in_lane) if speeds_in_lane else 0.0
            )

            density = vehicle_count / 20.0

            traffic_flow = vehicle_count * 60.0

            statistics.append(
                LaneStatistics(
                    lane_id=lane_id,
                    vehicle_count=vehicle_count,
                    average_speed=average_speed,
                    density=density,
                    queue_length=queue_length,
                    traffic_flow=traffic_flow,
                )
            )

        return statistics
