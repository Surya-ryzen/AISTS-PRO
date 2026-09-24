class VideoError(Exception):
    """Base exception for video ingestion."""

    pass


class VideoOpenError(VideoError):
    """Raised when the video source cannot be opened."""

    pass


class FrameReadError(VideoError):
    """Raised when a frame cannot be read."""

    pass


class VideoEndOfStream(VideoError):
    """Raised when a finite video source reaches the end."""

    pass
