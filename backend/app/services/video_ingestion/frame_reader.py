import cv2
import time

from .config import VideoConfig
from .exceptions import (
    VideoOpenError,
    FrameReadError,
    VideoEndOfStream,
)
from .models import Frame, VideoInfo


class FrameReader:
    """
    Reads frames from a video source.

    Supports:
    - MP4 videos
    - USB cameras
    - RTSP streams
    """

    def __init__(
        self,
        source: str | None = None,
        source_type: str | None = None,
    ):

        self.config = VideoConfig()

        if source is not None:
            self.config.source = source

        self.source_type = source_type

        self.capture = None

        self.frame_id = 0
        self.loop_index = 0

        self.video_info = None

    @property
    def fps(self):
        if self.video_info:
            return self.video_info.fps
        return self.config.target_fps

    def open(self):

        self.capture = cv2.VideoCapture(self.config.source)

        if not self.capture.isOpened():
            raise VideoOpenError(f"Unable to open video source: {self.config.source}")

        width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))

        height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fps = self.capture.get(cv2.CAP_PROP_FPS)

        if fps <= 0:
            fps = self.config.target_fps

        total_frames = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))

        if total_frames <= 0:
            total_frames = None

        self.video_info = VideoInfo(
            width=width,
            height=height,
            fps=fps,
            total_frames=total_frames,
            source=self.config.source,
        )

    def read(self):

        if self.capture is None:
            raise VideoOpenError("Video source is not opened.")

        success, image = self.capture.read()

        if not success:

            # -----------------------------
            # Local video file
            # -----------------------------
            if self._is_file_source():

                # Restart video when looping is enabled
                if self.config.loop_video:

                    self.loop_index += 1
                    self.capture.set(
                        cv2.CAP_PROP_POS_FRAMES,
                        0,
                    )

                    success, image = self.capture.read()

                    if not success:
                        raise FrameReadError("Unable to restart video source.")

                else:

                    raise VideoEndOfStream("End of video reached.")

            # -----------------------------
            # Live source
            # -----------------------------
            else:

                raise FrameReadError("Unable to read frame from live video source.")

        # -----------------------------
        # Resize frame
        # -----------------------------
        if image.shape[1] != self.config.width or image.shape[0] != self.config.height:
            image = cv2.resize(
                image,
                (
                    self.config.width,
                    self.config.height,
                ),
            )

        self.frame_id += 1

        return Frame(
            frame_id=self.frame_id,
            image=image,
            timestamp=time.time(),
            source_seconds=(max(0, self.capture.get(cv2.CAP_PROP_POS_FRAMES)-1)/self.fps if self._is_file_source() else None),
            loop_index=self.loop_index,
        )

    def _is_file_source(self) -> bool:
        """
        Returns True when the configured source
        is a local video file.
        """

        if self.source_type is not None:
            return self.source_type.lower() == "file"

        source = str(self.config.source).lower()

        return source.endswith((".mp4", ".avi", ".mov", ".mkv", ".webm"))

    def release(self):

        if self.capture is not None:
            self.capture.release()

        self.capture = None

    def is_open(self):

        return self.capture is not None and self.capture.isOpened()
