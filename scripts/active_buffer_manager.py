"""Active Buffer Manager: event-driven segment buffering.

Replaces fixed 10-second chunking. Frames are always flowing into a small
rolling pre-roll buffer; a segment is only opened, extended, and flushed to
disk in response to activity reported by the Lightweight Perception Layer,
not a wall-clock timer. Idle camera time costs nothing (no file written, no
Nemotron/Gemma call triggered); active periods are captured in full.

Long-running events are automatically ROTATED into consecutive segments
rather than being allowed to grow without bound, because oversized clips
cause hosted Nemotron inference to time out. Rotation is triggered by
whichever limit is hit first:

  * `max_event_duration_seconds` -- a configurable wall-clock cap on a
    single segment (default ~18s, recommended range 15-20s).
  * `max_segment_size_bytes` -- a configurable cap on the encoded file size
    of a single segment (default ~7MB).

When either limit is hit, the current segment is closed and dispatched
immediately, and -- if the event is still ongoing -- a new segment begins
recording with no gap in coverage. IncidentStateManager is responsible for
stitching the resulting consecutive segments back into one logical incident
on the global timeline.
"""

from __future__ import annotations

import logging
import sys
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from perception_layer import PerceptionResult

logger = logging.getLogger(__name__)


class BufferState(Enum):
    IDLE = auto()
    ACTIVE = auto()
    COOLDOWN = auto()


@dataclass
class FinalizedSegment:
    path: Path
    start_stream_seconds: float
    end_stream_seconds: float
    duration_seconds: float
    frame_count: int


@dataclass
class _PendingSegment:
    path: Path
    writer: cv2.VideoWriter
    frame_count: int = 0
    start_stream_seconds: float = 0.0
    last_active_seconds: float = 0.0


class ActiveBufferManager:
    """Event-driven frame buffer producing variable-length video segments."""

    def __init__(
        self,
        output_dir: str | Path,
        fps: int = 4,
        resolution: tuple[int, int] = (1280, 720),
        pre_roll_seconds: float = 2.0,
        post_roll_seconds: float = 3.0,
        min_segment_seconds: float = 1.5,
        max_event_duration_seconds: float = 18.0,
        max_segment_size_bytes: int = 7 * 1024 * 1024,
        size_check_every_n_frames: int = 4,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.fps = fps
        self.resolution = resolution
        self.pre_roll_seconds = pre_roll_seconds
        self.post_roll_seconds = post_roll_seconds
        self.min_segment_seconds = min_segment_seconds
        self.max_event_duration_seconds = max_event_duration_seconds
        self.max_segment_size_bytes = max_segment_size_bytes
        self.size_check_every_n_frames = max(1, size_check_every_n_frames)

        pre_roll_frames = max(1, int(round(pre_roll_seconds * fps)))
        self._pre_roll: deque[tuple[np.ndarray, float]] = deque(maxlen=pre_roll_frames)

        self._state = BufferState.IDLE
        self._pending: _PendingSegment | None = None
        self._segment_index = 0

    @property
    def state(self) -> BufferState:
        return self._state

    def add_frame(
        self, frame: np.ndarray, perception: PerceptionResult
    ) -> FinalizedSegment | None:
        """Feed one frame + its perception result. Returns a finalized
        segment whenever one is closed out -- either because the event
        ended, or because it was rotated for duration/size reasons."""
        resized = cv2.resize(frame, self.resolution)
        timestamp = perception.timestamp

        if self._state == BufferState.IDLE:
            self._pre_roll.append((resized, timestamp))
            if perception.is_active:
                self._open_segment(timestamp)
            return None

        assert self._pending is not None
        pending = self._pending
        pending.writer.write(resized)
        pending.frame_count += 1

        if perception.is_active:
            pending.last_active_seconds = timestamp
            self._state = BufferState.ACTIVE
        elif self._state == BufferState.ACTIVE:
            self._state = BufferState.COOLDOWN

        elapsed = timestamp - pending.start_stream_seconds
        since_last_active = timestamp - pending.last_active_seconds

        if pending.frame_count % self.size_check_every_n_frames == 0:
            current_size = self._current_pending_size()
            if current_size >= self.max_segment_size_bytes:
                return self._rotate(
                    timestamp, reason="size_cap", still_active=perception.is_active
                )

        if elapsed >= self.max_event_duration_seconds:
            return self._rotate(
                timestamp,
                reason="max_event_duration",
                still_active=perception.is_active,
            )

        if (
            self._state == BufferState.COOLDOWN
            and since_last_active >= self.post_roll_seconds
        ):
            return self._close_segment(timestamp, reason="activity_ended")

        return None

    def flush(self, timestamp: float) -> FinalizedSegment | None:
        """Force-close whatever segment is pending (e.g. on shutdown)."""
        if self._pending is None:
            return None
        return self._close_segment(timestamp, reason="forced_flush")

    def _current_pending_size(self) -> int:
        if self._pending is None:
            return 0
        try:
            return self._pending.path.stat().st_size
        except OSError:
            return 0

    def _open_segment(self, timestamp: float, is_continuation: bool = False) -> None:
        self._segment_index += 1
        path = self.output_dir / f"event_{self._segment_index:05d}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(path), fourcc, self.fps, self.resolution)

        pending = _PendingSegment(
            path=path,
            writer=writer,
            start_stream_seconds=timestamp,
            last_active_seconds=timestamp,
        )

        if not is_continuation and self._pre_roll:
            for pre_roll_frame, _pre_roll_timestamp in self._pre_roll:
                writer.write(pre_roll_frame)
                pending.frame_count += 1
            pending.start_stream_seconds = self._pre_roll[0][1]

        self._pending = pending
        self._pre_roll.clear()
        self._state = BufferState.ACTIVE

    def _rotate(
        self, timestamp: float, reason: str, still_active: bool
    ) -> FinalizedSegment | None:
        """Close the current segment and, if the event is still ongoing,
        immediately start a new one with no gap in coverage."""
        logger.info("Rotating event segment at t=%.2fs (reason=%s)", timestamp, reason)
        finalized = self._close_segment(timestamp, reason=reason)
        if still_active:
            self._open_segment(timestamp, is_continuation=True)
        return finalized

    def _close_segment(
        self, timestamp: float, reason: str
    ) -> FinalizedSegment | None:
        pending = self._pending
        self._pending = None
        self._state = BufferState.IDLE
        self._pre_roll.clear()

        if pending is None:
            return None

        pending.writer.release()

        if pending.frame_count == 0:
            self._safe_unlink(pending.path)
            return None

        duration = timestamp - pending.start_stream_seconds
        if duration < self.min_segment_seconds:
            # Too short to be a meaningful event; discard silently -- no
            # Nemotron/Gemma call is triggered for pure noise.
            self._safe_unlink(pending.path)
            return None

        logger.debug(
            "Segment %s finalized (reason=%s, duration=%.2fs, frames=%d)",
            pending.path.name,
            reason,
            duration,
            pending.frame_count,
        )

        return FinalizedSegment(
            path=pending.path,
            start_stream_seconds=round(pending.start_stream_seconds, 3),
            end_stream_seconds=round(timestamp, 3),
            duration_seconds=round(duration, 3),
            frame_count=pending.frame_count,
        )

    @staticmethod
    def _safe_unlink(path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Could not remove discarded segment file: %s", path)
