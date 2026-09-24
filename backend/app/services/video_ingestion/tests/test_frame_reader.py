import cv2

from backend.app.services.video_ingestion.service import VideoService


def main():

    video = VideoService()

    video.start()

    print("=" * 50)
    print("Video Information")
    print("=" * 50)

    print(video.video_info)

    while True:

        frame = video.get_frame()

        cv2.imshow(
            "Video Test",
            frame.image
        )

        delay = max(
            1,
            int(1000 / video.fps)
        )

        key = cv2.waitKey(delay)

        if key == ord("q"):
            break

    video.stop()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()