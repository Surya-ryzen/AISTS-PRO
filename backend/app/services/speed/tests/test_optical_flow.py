import cv2

from backend.app.services.video_ingestion.frame_reader import FrameReader

from backend.app.services.speed.config import SpeedConfig

from backend.app.services.speed.optical_flow import OpticalFlow


def main():

    reader = FrameReader()

    reader.open()

    config = SpeedConfig()

    optical_flow = OpticalFlow(
        config.optical_flow
    )

    while True:

        frame = reader.read()

        flow = optical_flow.compute(
            frame.image
        )

        cv2.imshow(
            "Traffic",
            frame.image
        )

        if flow is not None:

            print(flow.shape)

        if cv2.waitKey(1) == ord("q"):

            break

    reader.release()

    cv2.destroyAllWindows()


if __name__ == "__main__":

    main()