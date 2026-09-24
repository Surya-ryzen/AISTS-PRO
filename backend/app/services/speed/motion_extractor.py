import numpy as np


class MotionExtractor:
    """
    Extracts average motion inside a tracked object's bounding box.
    """

    @staticmethod
    def extract(flow, track):

        if flow is None:
            return None

        height, width = flow.shape[:2]

        # Keep bounding box inside image boundaries
        x1 = max(0, track.x1)
        y1 = max(0, track.y1)
        x2 = min(width, track.x2)
        y2 = min(height, track.y2)

        if x1 >= x2 or y1 >= y2:
            return None

        # Crop the flow matrix to the vehicle region
        roi = flow[y1:y2, x1:x2]

        if roi.size == 0:
            return None

        # Average motion vector (dx, dy)
        mean_dx = np.mean(roi[:, :, 0])
        mean_dy = np.mean(roi[:, :, 1])

        return mean_dx, mean_dy