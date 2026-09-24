from .frame_reader import FrameReader


class VideoService:
    """
    High-level interface for video ingestion.
    """

    def __init__(
        self,
        source: str | None = None,
        source_type: str | None = None,
    ):

        self.reader = FrameReader(
            source=source,
            source_type=source_type,
        )

    def start(self):

        self.reader.open()

    def get_frame(self):

        return self.reader.read()

    def stop(self):

        self.reader.release()

    @property
    def fps(self):

        return self.reader.fps

    @property
    def video_info(self):

        return self.reader.video_info
