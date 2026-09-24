import cv2


class Visualizer:

    @staticmethod
    def draw_tracks(image, tracks):

        output = image.copy()

        for track in tracks:

            cv2.rectangle(
                output,
                (track.x1, track.y1),
                (track.x2, track.y2),
                (0, 255, 0),
                2
            )

            label = f"{track.class_name} ID:{track.track_id}"

            cv2.putText(
                output,
                label,
                (track.x1, track.y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        return output

    @staticmethod
    def draw_detections(image, detections):

        output = image.copy()

        for detection in detections:

            cv2.rectangle(
                output,
                (detection.x1, detection.y1),
                (detection.x2, detection.y2),
                (255, 0, 0),
                2
            )

            label = (
                f"{detection.class_name} "
                f"{detection.confidence:.2f}"
            )

            cv2.putText(
                output,
                label,
                (detection.x1, detection.y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 0, 0),
                2
            )

        return output