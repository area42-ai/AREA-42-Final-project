"""Evidence Manager: extracts and persists keyframe evidence for incidents.

Pulls representative frames directly from the finalized event segment video
(the same file Pipeline A analyzed) at the moments an incident starts,
resolves, or is confirmed still ongoing, and attaches file references into
each incident's `evidence` list in the merged timeline document -- without
altering the incident_contract schema (evidence is already a declared,
open-ended list field there).

Only attaches "still ongoing" evidence for incidents that the Incident State
Manager confirmed were actually touched by THIS segment (touched_incident_ids)
so a stale, unrelated open incident never gets a misleading keyframe from a
segment it wasn't part of.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Iterable

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent))
from active_buffer_manager import FinalizedSegment


class EvidenceManager:
    def __init__(self, evidence_dir: str | Path) -> None:
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def attach_evidence(
        self,
        document: dict[str, Any],
        segment: FinalizedSegment,
        touched_incident_ids: Iterable[str] = (),
    ) -> None:
        """Mutates `document` in place, appending keyframe evidence entries
        to any incident whose global timeline overlaps this segment."""
        touched = set(touched_incident_ids)
        segment_start = segment.start_stream_seconds
        segment_end = segment.end_stream_seconds

        capture = cv2.VideoCapture(str(segment.path))
        try:
            fps = capture.get(cv2.CAP_PROP_FPS) or 4.0
            for incident in document.get("incidents", []):
                self._attach_for_incident(
                    incident, capture, fps, segment_start, segment_end, segment, touched
                )
        finally:
            capture.release()

    def _attach_for_incident(
        self,
        incident: dict[str, Any],
        capture: cv2.VideoCapture,
        fps: float,
        segment_start: float,
        segment_end: float,
        segment: FinalizedSegment,
        touched: set[str],
    ) -> None:
        moments: list[tuple[str, float]] = []

        start_global = incident.get("start_seconds")
        end_global = incident.get("end_seconds")
        incident_id = incident.get("incident_id", "incident")

        if start_global is not None and segment_start <= start_global <= segment_end:
            moments.append(("violation_start", start_global))

        if end_global is not None and segment_start <= end_global <= segment_end:
            moments.append(("violation_resolved", end_global))

        if (
            not moments
            and end_global is None
            and start_global is not None
            and start_global < segment_start
            and incident_id in touched
        ):
            # Confirmed by this segment as still ongoing from an earlier
            # segment -- capture proof near the end of this segment.
            moments.append(("still_missing", max(segment_start, segment_end - 0.25)))

        if not moments:
            return

        existing_paths = {entry.get("path") for entry in incident.get("evidence", [])}

        for label, global_timestamp in moments:
            local_timestamp = global_timestamp - segment_start
            frame = self._grab_frame(capture, fps, local_timestamp)
            if frame is None:
                continue

            filename = f"{incident_id}_{label}_{global_timestamp:.2f}.jpg"
            out_path = self.evidence_dir / filename
            if str(out_path) in existing_paths:
                continue

            cv2.imwrite(str(out_path), frame)
            incident.setdefault("evidence", []).append(
                {
                    "type": label,
                    "path": str(out_path),
                    "timestamp_seconds": round(global_timestamp, 3),
                    "source_segment": segment.path.name,
                }
            )

    @staticmethod
    def _grab_frame(capture: cv2.VideoCapture, fps: float, local_timestamp: float):
        frame_index = max(0, int(round(local_timestamp * fps)))
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = capture.read()
        return frame if ok else None
