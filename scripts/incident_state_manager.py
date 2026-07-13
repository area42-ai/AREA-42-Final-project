"""Incident State Manager: cross-segment incident continuity.

Pipeline A (Nemotron -> Gemma -> incident_contract) still produces one
self-contained, contract-valid document PER event segment, exactly as
before -- nothing about Pipeline A's internals changes. This module is what
turns a stream of independent per-segment documents into a single, coherent,
continuously-updated incident timeline for the whole live stream: an open
violation that spans a segment boundary is extended rather than reported as
two disconnected incidents, and a violation that clears is closed out
exactly once, in the correct place on the global timeline.

All timestamps handled internally and in the persisted output are on the
GLOBAL stream timeline (shifted by segment.start_stream_seconds), never
segment-local.
"""

from __future__ import annotations

import json
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from active_buffer_manager import FinalizedSegment
from incident_contract import (
    STATUS_RESOLVED,
    STATUS_UNRESOLVED,
    build_envelope,
    build_incident,
    validate_document,
)


@dataclass
class _OpenIncident:
    ppe_item: str
    person_id: Any
    start_seconds: float
    last_seen_seconds: float
    minimum_confirmed_duration_seconds: float | None
    confidence: float | None
    action_sequence: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)


class IncidentStateManager:
    """Stateful stitcher maintaining one running incident timeline per stream."""

    def __init__(
        self,
        video_id: str,
        timeline_path: str | Path,
        continuity_gap_seconds: float = 4.0,
        stale_timeout_seconds: float = 30.0,
    ) -> None:
        self.video_id = video_id
        self.timeline_path = Path(timeline_path)
        self.timeline_path.parent.mkdir(parents=True, exist_ok=True)
        self.continuity_gap_seconds = continuity_gap_seconds
        self.stale_timeout_seconds = stale_timeout_seconds

        self._lock = threading.Lock()
        self._open: dict[tuple[Any, str], _OpenIncident] = {}
        self._closed: list[dict[str, Any]] = []
        self._models_seen: list[str] = []
        self._analysis_scope: list[str] = []
        self._last_key_to_id: dict[tuple[Any, str], str] = {}

    def open_incident_count(self) -> int:
        with self._lock:
            return len(self._open)

    def ingest_segment(
        self,
        incident_json_path: Path,
        segment: FinalizedSegment,
    ) -> tuple[dict[str, Any], set[str]]:
        """Merge one segment's Pipeline A output into the running timeline.

        Returns (merged_document, touched_incident_ids). Does NOT persist to
        disk (call persist() for that) so callers can attach evidence first.
        touched_incident_ids identifies which incidents in the rebuilt
        document were actually confirmed by THIS segment, so the Evidence
        Manager never attaches a keyframe from an unrelated segment to an
        incident it didn't observe.
        """
        segment_document = json.loads(incident_json_path.read_text(encoding="utf-8"))
        errors = validate_document(segment_document)
        if errors:
            raise ValueError(
                f"Segment document {incident_json_path} failed contract "
                f"validation: {errors}"
            )

        offset = segment.start_stream_seconds
        segment_end_global = segment.end_stream_seconds

        with self._lock:
            self._remember_models(segment_document.get("models", []))
            self._remember_scope(segment_document.get("analysis_scope", []))

            touched_keys: set[tuple[Any, str]] = set()

            for incident in segment_document.get("incidents", []):
                shifted = _shift_incident(incident, offset)
                key = (shifted["person_id"], shifted["violated_items"][0])
                touched_keys.add(key)
                self._merge_incident(key, shifted, segment_end_global)

            self._expire_stale(segment_end_global, exclude=touched_keys)

            document = self._rebuild_document()
            touched_ids = {
                self._last_key_to_id[key]
                for key in touched_keys
                if key in self._last_key_to_id
            }
            return document, touched_ids

    def persist(self, document: dict[str, Any] | None = None) -> Path:
        with self._lock:
            doc = document if document is not None else self._rebuild_document()
        self.timeline_path.write_text(
            json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return self.timeline_path

    def finalize(self) -> dict[str, Any]:
        """Close out every still-open incident (e.g. on stream shutdown)."""
        with self._lock:
            for key in list(self._open.keys()):
                self._close_open(key, end_seconds=None)
            return self._rebuild_document()

    # -- internals -----------------------------------------------------

    def _remember_models(self, models: list[Any]) -> None:
        for model in models:
            if isinstance(model, str) and model not in self._models_seen:
                self._models_seen.append(model)

    def _remember_scope(self, scope: list[Any]) -> None:
        for item in scope:
            if item not in self._analysis_scope:
                self._analysis_scope.append(item)

    def _merge_incident(
        self,
        key: tuple[Any, str],
        shifted: dict[str, Any],
        segment_end_global: float,
    ) -> None:
        person_id, ppe_item = key
        existing = self._open.get(key)

        if existing is not None:
            gap = shifted["start_seconds"] - existing.last_seen_seconds
            if gap > self.continuity_gap_seconds:
                # Too large a gap to be the same continuous violation;
                # close the stale one out and start fresh below.
                self._close_open(key, end_seconds=None)
                existing = None

        if existing is not None:
            existing.action_sequence.extend(shifted.get("action_sequence", []))
            existing.evidence.extend(shifted.get("evidence", []))
            if existing.confidence is None:
                existing.confidence = shifted.get("confidence")

            if shifted["status"] == STATUS_RESOLVED:
                self._close_open(key, end_seconds=shifted["end_seconds"])
            else:
                self._update_open_minimum(existing, shifted, segment_end_global)
            return

        # No open incident for this key: register one.
        if shifted["status"] == STATUS_RESOLVED:
            self._closed.append(
                _finalized_incident_dict(
                    person_id=person_id,
                    ppe_item=ppe_item,
                    start_seconds=shifted["start_seconds"],
                    end_seconds=shifted["end_seconds"],
                    minimum_confirmed_duration_seconds=shifted.get(
                        "minimum_confirmed_duration_seconds"
                    ),
                    confidence=shifted.get("confidence"),
                    action_sequence=shifted.get("action_sequence", []),
                    evidence=shifted.get("evidence", []),
                )
            )
        else:
            self._open[key] = _OpenIncident(
                ppe_item=ppe_item,
                person_id=person_id,
                start_seconds=shifted["start_seconds"],
                last_seen_seconds=segment_end_global,
                minimum_confirmed_duration_seconds=shifted.get(
                    "minimum_confirmed_duration_seconds"
                ),
                confidence=shifted.get("confidence"),
                action_sequence=list(shifted.get("action_sequence", [])),
                evidence=list(shifted.get("evidence", [])),
            )

    def _update_open_minimum(
        self,
        existing: _OpenIncident,
        shifted: dict[str, Any],
        segment_end_global: float,
    ) -> None:
        # An incident still unresolved at the end of another segment is, at
        # minimum, confirmed missing through that segment's end.
        candidates = [segment_end_global - existing.start_seconds]
        if shifted.get("minimum_confirmed_duration_seconds") is not None:
            candidates.append(float(shifted["minimum_confirmed_duration_seconds"]))
        if existing.minimum_confirmed_duration_seconds is not None:
            candidates.append(existing.minimum_confirmed_duration_seconds)
        existing.minimum_confirmed_duration_seconds = round(max(candidates), 3)
        existing.last_seen_seconds = max(existing.last_seen_seconds, segment_end_global)

    def _close_open(self, key: tuple[Any, str], end_seconds: float | None) -> None:
        existing = self._open.pop(key, None)
        if existing is None:
            return
        self._closed.append(
            _finalized_incident_dict(
                person_id=existing.person_id,
                ppe_item=existing.ppe_item,
                start_seconds=existing.start_seconds,
                end_seconds=end_seconds,
                minimum_confirmed_duration_seconds=existing.minimum_confirmed_duration_seconds,
                confidence=existing.confidence,
                action_sequence=existing.action_sequence,
                evidence=existing.evidence,
            )
        )

    def _expire_stale(
        self, now_global: float, exclude: set[tuple[Any, str]]
    ) -> None:
        stale_keys = [
            key
            for key, incident in self._open.items()
            if key not in exclude
            and (now_global - incident.last_seen_seconds) > self.stale_timeout_seconds
        ]
        for key in stale_keys:
            self._close_open(key, end_seconds=None)

    def _rebuild_document(self) -> dict[str, Any]:
        open_as_incidents = [
            _finalized_incident_dict(
                person_id=incident.person_id,
                ppe_item=incident.ppe_item,
                start_seconds=incident.start_seconds,
                end_seconds=None,
                minimum_confirmed_duration_seconds=incident.minimum_confirmed_duration_seconds,
                confidence=incident.confidence,
                action_sequence=incident.action_sequence,
                evidence=incident.evidence,
            )
            for incident in self._open.values()
        ]

        all_incidents = sorted(
            self._closed + open_as_incidents,
            key=lambda item: item["start_seconds"],
        )

        built: list[dict[str, Any]] = []
        key_to_id: dict[tuple[Any, str], str] = {}
        for position, incident in enumerate(all_incidents, start=1):
            incident_id = f"incident_{position:03d}"
            key = (incident["person_id"], incident["violated_items"][0])
            key_to_id[key] = incident_id
            built.append(
                build_incident(
                    index=position,
                    ppe_item=incident["violated_items"][0],
                    start_seconds=incident["start_seconds"],
                    end_seconds=incident["end_seconds"],
                    status=(
                        STATUS_RESOLVED
                        if incident["end_seconds"] is not None
                        else STATUS_UNRESOLVED
                    ),
                    minimum_confirmed_duration_seconds=incident[
                        "minimum_confirmed_duration_seconds"
                    ],
                    confidence=incident["confidence"],
                    action_sequence=incident["action_sequence"],
                    evidence=incident["evidence"],
                    person_id=incident["person_id"],
                )
            )

        self._last_key_to_id = key_to_id

        document = build_envelope(
            video_id=self.video_id,
            source_pipeline="nemotron_gemma",
            models=self._models_seen,
            analysis_scope=self._analysis_scope,
            incidents=built,
            summary=(
                f"Live event-driven timeline: {len(built)} incident(s) "
                "across all processed segments."
            ),
            quality={
                "parse_success": True,
                "planned_frames": None,
                "analyzed_frames": None,
                "status_counts": {},
                "warnings": [],
            },
        )

        errors = validate_document(document)
        if errors:
            raise ValueError(f"Rebuilt timeline failed contract validation: {errors}")
        return document


def _shift_incident(incident: dict[str, Any], offset: float) -> dict[str, Any]:
    shifted = dict(incident)
    shifted["start_seconds"] = round(incident["start_seconds"] + offset, 3)
    shifted["end_seconds"] = (
        round(incident["end_seconds"] + offset, 3)
        if incident.get("end_seconds") is not None
        else None
    )
    shifted["action_sequence"] = [
        {
            **event,
            "timestamp_seconds": round(
                event.get("timestamp_seconds", 0.0) + offset, 3
            ),
        }
        for event in incident.get("action_sequence", [])
    ]
    return shifted


def _finalized_incident_dict(
    *,
    person_id: Any,
    ppe_item: str,
    start_seconds: float,
    end_seconds: float | None,
    minimum_confirmed_duration_seconds: float | None,
    confidence: float | None,
    action_sequence: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "person_id": person_id,
        "violated_items": [ppe_item],
        "start_seconds": start_seconds,
        "end_seconds": end_seconds,
        "minimum_confirmed_duration_seconds": minimum_confirmed_duration_seconds,
        "confidence": confidence,
        "action_sequence": action_sequence,
        "evidence": evidence,
    }
