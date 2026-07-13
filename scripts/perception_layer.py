"""Lightweight Perception Layer.

Cheap, dependency-light per-frame analysis used to decide WHEN something is
happening in front of the camera, so the pipeline stops paying for fixed
10-second Nemotron/Gemma calls on empty video. This layer never makes PPE or
compliance decisions -- it only answers "is there something worth looking
at right now?" for the Active Buffer Manager.

Runs on every captured frame in-process (no external API calls, no heavy
model weights): OpenCV background subtraction for motion, and OpenCV's
built-in HOG person detector (sampled at a lower rate, since it is far more
expensive than background subtraction) for presence confirmation.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class PerceptionResult:
    timestamp: float  # stream-time seconds since capture start
    motion_score: float  # smoothed 0..1 ratio of foreground pixels
    person_present: bool | None  # None when not sampled this frame
    is_active: bool  # final decision after debouncing/thresholds


class PerceptionLayer:
    """Cheap motion + presence gate that drives event-driven buffering."""

    def __init__(
        self,
        motion_threshold: float = 0.015,
        activation_ema_alpha: float = 0.35,
        person_sample_every_n_frames: int = 6,
        history: int = 300,
        var_threshold: float = 16.0,
    ) -> None:
        self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=history, varThreshold=var_threshold, detectShadows=False
        )
        self._hog = cv2.HOGDescriptor()
        self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        self.motion_threshold = motion_threshold
        self.activation_ema_alpha = activation_ema_alpha
        self.person_sample_every_n_frames = max(1, person_sample_every_n_frames)

        self._smoothed_motion = 0.0
        self._frame_index = 0
        self._last_person_present: bool | None = None

    def process_frame(self, frame: np.ndarray, timestamp: float) -> PerceptionResult:
        self._frame_index += 1

        fg_mask = self._bg_subtractor.apply(frame)
        foreground_ratio = float(np.count_nonzero(fg_mask)) / float(fg_mask.size)

        self._smoothed_motion = (
            self.activation_ema_alpha * foreground_ratio
            + (1.0 - self.activation_ema_alpha) * self._smoothed_motion
        )

        person_present = self._last_person_present
        if self._frame_index % self.person_sample_every_n_frames == 0:
            person_present = self._detect_person(frame)
            self._last_person_present = person_present

        motion_active = self._smoothed_motion >= self.motion_threshold
        is_active = motion_active or bool(person_present)

        return PerceptionResult(
            timestamp=timestamp,
            motion_score=round(self._smoothed_motion, 4),
            person_present=person_present,
            is_active=is_active,
        )

    def _detect_person(self, frame: np.ndarray) -> bool:
        small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rects, _weights = self._hog.detectMultiScale(
            small, winStride=(8, 8), padding=(8, 8), scale=1.05
        )
        return len(rects) > 0
