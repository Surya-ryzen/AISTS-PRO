import cv2
import numpy as np


class OpticalFlow:

    """
    Computes dense optical flow between
    consecutive frames using Farneback.
    """

    def __init__(self, config):

        self.config = config

        self.previous_gray = None

    def compute(self, frame):

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        if self.previous_gray is None:

            self.previous_gray = gray

            return None

        flow = cv2.calcOpticalFlowFarneback(

            self.previous_gray,

            gray,

            None,

            pyr_scale=self.config["pyr_scale"],

            levels=self.config["levels"],

            winsize=self.config["winsize"],

            iterations=self.config["iterations"],

            poly_n=self.config["poly_n"],

            poly_sigma=self.config["poly_sigma"],

            flags=0
        )

        self.previous_gray = gray

        return flow