"""Conservative motion-calibrated ROI; this is not semantic divider detection."""

from collections import deque
from pathlib import Path

import cv2
import numpy as np
import yaml

from .models import ROI


class ROIService:
    def __init__(self):
        path = Path("configs/roi.yaml")
        self.config = yaml.safe_load(path.read_text())["roi"] if path.exists() else {}
        self.reset()

    def reset(self, source=None):
        self.source = str(source or "")
        self.manual_lanes = []
        self.profile = None
        path = Path("configs/roi-profiles.local")
        if path.exists():
            profiles = yaml.safe_load(path.read_text()) or {}
            self.profile = profiles.get(self.source)
        self.roi = ROI([])
        self.histories = {}
        self.last_seen = {}
        self.frame_number = 0
        self.direction = None
        self.ready = False
        self.shape = None
        self.status = "Learning road movement - counts paused"
        self.lane_boundaries = []
        self.lane_count = 0

    def _motion(self, points):
        if len(points) < 6:
            return None
        a = np.asarray(points, dtype=float)
        delta = np.median(a[-3:, :2], axis=0) - np.median(a[:3, :2], axis=0)
        distance = np.linalg.norm(delta)
        if (
            distance
            < self.config.get("minimum_motion_pixels", 8) * self.shape[1] / 1280
        ):
            return None
        return delta / distance

    def update(self, image, tracks):
        shape = image.shape[:2]
        if self.shape is not None and self.shape != shape:
            self.reset(self.source)
        self.shape = shape
        if self.profile and self.profile.get("disabled"):
            self.status = "Road removed - draw and save a road to resume counting"
            self.ready = False
            return []
        if self.profile and not self.ready:
            h, w = shape
            self.roi.points = [
                (int(x * (w - 1)), int(y * (h - 1))) for x, y in self.profile["polygon"]
            ]
            self.manual_lanes = [
                [(int(x * (w - 1)), int(y * (h - 1))) for x, y in lane]
                for lane in self.profile["lanes"]
            ]
            self.lane_count = len(self.manual_lanes)
            self.ready = True
            self.status = (f"Reviewed road region - {self.lane_count} configured lanes" if self.manual_lanes else "Saved road region - learning traffic bands")
        self.frame_number += 1
        for track in tracks:
            point = (
                (track.x1 + track.x2) / 2,
                track.y2,
                max(1, (track.x2 - track.x1) * (track.y2 - track.y1)),
            )
            self.histories.setdefault(track.track_id, deque(maxlen=80)).append(point)
            self.last_seen[track.track_id] = self.frame_number
        for key in list(self.histories):
            if self.frame_number - self.last_seen[key] > 160:
                del self.histories[key]
                del self.last_seen[key]
        if not self.ready and self.frame_number >= self.config.get(
            "calibration_frames", 60
        ):
            if self.frame_number % 10 == 0:
                self._calibrate()
        if self.profile and not self.manual_lanes and not self.lane_count and self.frame_number >= 60:
            samples = [(key, self._motion(points)) for key, points in self.histories.items()
                       if self.contains(points[-1][0], points[-1][1])]
            samples = [(key, motion) for key, motion in samples if motion is not None]
            if len(samples) >= 4:
                self._estimate_lanes(samples, [True]*len(samples))
                self.status = f"Saved ROI - {self.lane_count} estimated traffic bands (review lanes)"
        return self.filter_tracks(tracks)

    def _calibrate(self):
        samples = [
            (key, self._motion(points)) for key, points in self.histories.items()
        ]
        samples = [
            (key, direction) for key, direction in samples if direction is not None
        ]
        minimum = self.config.get("minimum_tracks", 4)
        if len(samples) < minimum:
            self.status = "Need more moving vehicles - counts paused"
            return
        vectors = np.asarray([v for _, v in samples])
        # The largest nearby vehicles define the carriageway of interest.
        weights = np.asarray(
            [np.median(np.asarray(self.histories[k])[:, 2]) for k, _ in samples]
        )
        mode = self.config.get("direction", "nearest")
        allowed = np.ones(len(samples), dtype=bool)
        if mode == "approaching":
            allowed = vectors[:, 1] > 0.25
        elif mode == "away":
            allowed = vectors[:, 1] < -0.25
        if not allowed.any():
            self.status = "Selected direction not observed - counts paused"
            return
        agreement = vectors @ vectors.T > 0.65
        scores = agreement @ weights
        scores[~allowed] = -1
        seed = int(scores.argmax())
        selected = agreement[seed] & allowed
        vertical = abs(vectors[seed, 1]) >= 0.45
        if vertical:
            selected = (vectors[:, 1] * vectors[seed, 1] > 0.10) & allowed
        if selected.sum() < minimum:
            self.status = "Road direction uncertain - counts paused"
            return
        direction = np.average(vectors[selected], axis=0, weights=weights[selected])
        direction /= np.linalg.norm(direction)
        if vertical:
            direction = np.array([0.0, np.sign(vectors[seed, 1])])
        points = np.asarray(
            [
                p[:2]
                for (key, _), keep in zip(samples, selected)
                if keep
                for p in self.histories[key]
            ],
            dtype=np.float32,
        )
        hull = cv2.convexHull(points).reshape(-1, 2)
        h, w = self.shape
        if cv2.contourArea(hull) < h * w * 0.025:
            self.status = "Road coverage too small - counts paused"
            return
        # Do not expand the hull: padding could cross an unseen divider.
        self.roi.points = [
            (int(np.clip(x, 0, w - 1)), int(np.clip(y, 0, h - 1))) for x, y in hull
        ]
        self.direction = direction
        self.ready = True
        self._estimate_lanes(samples, selected)
        self.status = f"Auto estimate: {self.lane_count} occupied lanes - review road/lane boundaries"

    def _estimate_lanes(self, samples, selected):
        # Estimate occupied traffic bands from trajectories, not physical lane markings.
        positions = []
        for (key, _), keep in zip(samples, selected):
            if not keep:
                continue
            fractions = []
            for x, y, _ in self.histories[key]:
                span = self.span(y)
                if span and span[1] - span[0] > self.shape[1] * 0.15:
                    fractions.append((x - span[0]) / (span[1] - span[0]))
            if fractions:
                positions.append(float(np.median(fractions)))
        groups = []
        for value in sorted(positions):
            if not groups or value - groups[-1][-1] > 0.17:
                groups.append([value])
            else:
                groups[-1].append(value)
        centers = [float(np.mean(group)) for group in groups] or [0.5]
        self.lane_boundaries = [(a + b) / 2 for a, b in zip(centers, centers[1:])]
        self.lane_count = len(centers)

    def contains(self, x, y):
        return (
            self.ready
            and cv2.pointPolygonTest(
                np.asarray(self.roi.points, dtype=np.float32),
                (float(x), float(y)),
                False,
            )
            >= 0
        )

    def filter_tracks(self, tracks):
        if not self.ready:
            return []
        result = []
        for track in tracks:
            if not self.contains((track.x1 + track.x2) / 2, track.y2):
                continue
            direction = self._motion(self.histories.get(track.track_id, []))
            # Unknown/stationary tracks are accepted only inside the learned region.
            if (
                self.direction is not None
                and direction is not None
                and float(direction @ self.direction) < 0.3
            ):
                continue
            result.append(track)
        return result

    def span(self, y):
        if not self.ready:
            return None
        xs = []
        points = self.roi.points
        for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
            if y1 != y2 and min(y1, y2) <= y <= max(y1, y2):
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        return (min(xs), max(xs)) if len(xs) >= 2 else None

    def counting_line(self):
        if not self.ready:
            return None
        ys = [p[1] for p in self.roi.points]
        y = int(min(ys) + 0.65 * (max(ys) - min(ys)))
        span = self.span(y)
        return ((int(span[0]), y), (int(span[1]), y)) if span else None

    def assign_lane(self, track):
        if not self.lane_count:
            track.lane_id = None
            return
        if self.manual_lanes:
            point = (float((track.x1 + track.x2) / 2), float(track.y2))
            track.lane_id = next(
                (
                    i + 1
                    for i, lane in enumerate(self.manual_lanes)
                    if cv2.pointPolygonTest(
                        np.asarray(lane, dtype=np.float32), point, False
                    )
                    >= 0
                ),
                None,
            )
            return
        span = self.span(track.y2)
        if span and span[1] > span[0]:
            fraction = ((track.x1 + track.x2) / 2 - span[0]) / (span[1] - span[0])
            track.lane_id = 1 + sum(
                fraction > boundary for boundary in self.lane_boundaries
            )

    def draw(self, image):
        if self.ready:
            cv2.polylines(
                image,
                [np.asarray(self.roi.points, dtype=np.int32)],
                True,
                (0, 0, 255),
                2,
            )
            for i, lane in enumerate(self.manual_lanes):
                cv2.polylines(
                    image, [np.asarray(lane, dtype=np.int32)], True, (255, 220, 0), 2
                )
                center = np.mean(lane, axis=0).astype(int)
                cv2.putText(
                    image,
                    f"Lane {i+1}",
                    tuple(center),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 220, 0),
                    2,
                )
            ys = [p[1] for p in self.roi.points]
            for boundary in self.lane_boundaries:
                points = []
                for y in np.linspace(min(ys) + 1, max(ys) - 1, 35):
                    span = self.span(y)
                    if span:
                        points.append(
                            (int(span[0] + boundary * (span[1] - span[0])), int(y))
                        )
                if len(points) > 1:
                    cv2.polylines(
                        image,
                        [np.asarray(points, dtype=np.int32)],
                        False,
                        (255, 220, 0),
                        2,
                    )
        y = image.shape[0] - 18
        cv2.rectangle(
            image, (0, y - 24), (image.shape[1], image.shape[0]), (25, 25, 25), -1
        )
        cv2.putText(
            image,
            self.status,
            (15, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 220, 255),
            2,
        )
        return image

