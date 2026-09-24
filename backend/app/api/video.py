import cv2
import time

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.app.dependencies.system import get_system
from backend.app.services.system.service import TrafficSystemService
from backend.app.database.tables.user import User
from backend.app.dependencies.auth import get_current_user

router = APIRouter(
    tags=["Video Stream"],
)


def generate_frames(
    system: TrafficSystemService,
):

    while system.running:

        image = system.get_latest_image()

        if image is None:
            time.sleep(0.01)
            continue

        success, buffer = cv2.imencode(
            ".jpg",
            image,
        )

        if not success:
            time.sleep(0.01)
            continue

        frame = buffer.tobytes()

        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

        # Prevent the streaming loop from
        # consuming CPU unnecessarily.
        time.sleep(0.03)


@router.get(
    "/video",
    summary="Stream processed traffic video",
)
def video(
    system: TrafficSystemService = Depends(get_system),
    current_user: User = Depends(get_current_user),
):

    return StreamingResponse(
        generate_frames(system),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get(
    "/video-preview",
    summary="Preview processed traffic video",
)
def video_preview(
    system: TrafficSystemService = Depends(get_system),
):
    return StreamingResponse(
        generate_frames(system),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
