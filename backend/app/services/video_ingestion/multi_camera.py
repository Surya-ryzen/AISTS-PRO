from backend.app.services.video_ingestion.service import VideoService


class MultiCameraService:
    """
    Manages multiple video sources belonging to one junction.

    Each camera is identified by its lane_id.
    """

    def __init__(self, cameras):

        self.videos: dict[int, VideoService] = {}

        for camera in cameras:

            self.videos[camera.lane_id] = VideoService(
                source=camera.source,
                source_type=camera.source_type,
            )

    def start(self):
        """
        Start all configured camera streams.
        """

        for video in self.videos.values():
            video.start()

    def stop(self):
        """
        Stop all configured camera streams.
        """

        for video in self.videos.values():
            video.stop()

    def get_frame(self, lane_id: int):
        """
        Get the latest frame from a specific lane.
        """

        video = self.videos.get(lane_id)

        if video is None:
            return None

        return video.get_frame()

    def get_frames(self):
        """
        Read one frame from every configured lane.

        Returns:
            Dictionary mapping lane_id to Frame.
        """

        frames = {}

        for lane_id, video in self.videos.items():

            frames[lane_id] = video.get_frame()

        return frames

    def get_video(self, lane_id: int):
        """
        Return the VideoService for a specific lane.
        """

        return self.videos.get(lane_id)

    @property
    def lane_ids(self):
        """
        Returns the configured lane IDs.
        """

        return sorted(self.videos.keys())

    @property
    def camera_count(self):
        """
        Returns the number of configured cameras.
        """

        return len(self.videos)
