from backend.app.services.analytics.calculators.base_calculator import BaseCalculator


class VehicleCounter(BaseCalculator):

    NAME = "Vehicle Counter"

    def __init__(self):

        self.current_count = 0
        self.unique_tracks = set()

    def calculate(self, frame, tracks, speeds, statistics):

        self.current_count = len(tracks)

        for track in tracks:
            self.unique_tracks.add(track.track_id)

        statistics.current_vehicle_count = self.current_count
        statistics.total_vehicle_count = len(self.unique_tracks)

        return statistics

    def reset(self):

        self.current_count = 0
        self.unique_tracks.clear()
