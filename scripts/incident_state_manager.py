"""Incident State Manager: cross-segment incident continuity.

Pipeline A (Nemotron -> Gemma -> incident_contract) still produces one
self-contained, contract-valid document PER event segment, exactly as
before -- nothing about Pipeline A's internals changes. This module turns a
stream of independent per-segment documents into a single, coherent,
continuously-updated incident timeline for the whole live stream.

Key design: incidents are keyed by PERSON only. All PPE items missing for
that person accumulate in violated_items (union across segments). A person
still violating after escalation_timeout_seconds triggers a NEW escalated
incident so the operator sees a fresh alert. Different people generate
separate independent incidents.
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
    violated_items: set[str]
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
        continuity_gap_seconds: float = 120.0,
        stale_timeout_seconds: float = 300.0,
        escalation_timeout_seconds: float = 120.0,
    ) -> None:
        self.video_id = video_id
        self.timeline_path = Path(timeline_path)
        self.timeline_path.parent.mkdir(parents=True, exist_ok=True)
        self.continuity_gap_seconds = continuity_gap_seconds
        self.stale_timeout_seconds = stale_timeout_seconds
        self.escalation_timeout_seconds = escalation_timeout_seconds

        self._lock = threading.Lock()
        # Key = person_id (str/int) or "anonymous" when person_id is None.
        self._open: dict[Any, _OpenIncident] = {}
        self._closed: list[dict[str, Any]] = []
        self._models_seen: list[str] = []
        self._analysis_scope: list[str] = []
        self._last_key_to_id: dict[Any, str] = {}

    def open_incident_count(self) -> int:
        with self._lock:
            return len(self._open)

    def ingest_segment(
        self,
        incident_json_path: Path,
        segment: FinalizedSegment,
    ) -> tuple[dict[str, Any], set[str]]:
        """Merge one segment's Pipeline A output into the running timeline."""
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

            touched_keys: set[Any] = set()

            for incident in segment_document.get("incidents", []):
                shifted = _shift_incident(incident, offset)
                person_id = shifted["person_id"]
                key = person_id if person_id is not None else "anonymous"
                touched_keys.add(key)
                self._merge_incident(key, person_id, shifted, segment_end_global)

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
        key: Any,
        person_id: Any,
        shifted: dict[str, Any],
        segment_end_global: float,
    ) -> None:
        new_violated = set(shifted.get("violated_items", []))
        existing = self._open.get(key)

        if existing is not None:
            gap = shifted["start_seconds"] - existing.last_seen_seconds
            if gap > self.continuity_gap_seconds:
                # Gap too large — close stale incident, start fresh below.
                self._close_open(key, end_seconds=None)
                existing = None

        if existing is not None:
            # Escalation: if the person has been violating too long, close and reopen.
            elapsed = segment_end_global - existing.start_seconds
            if elapsed > self.escalation_timeout_seconds:
                saved_violated = set(existing.violated_items)
                self._close_open(key, end_seconds=existing.last_seen_seconds)
                # Reopen as escalation with accumulated violated_items.
                self._open[key] = _OpenIncident(
                    violated_items=saved_violated | new_violated,
                    person_id=person_id,
                    start_seconds=segment_end_global,
                    last_seen_seconds=segment_end_global,
                    minimum_confirmed_duration_seconds=None,
                    confidence=shifted.get("confidence"),
                    action_sequence=list(shifted.get("action_sequence", [])),
                    evidence=list(shifted.get("evidence", [])),
                )
                return

            # Normal merge: union of violated items, extend sequences.
            existing.violated_items.update(new_violated)
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
                    violated_items=new_violated,
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
                violated_items=new_violated,
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
        candidates = [segment_end_global - existing.start_seconds]
        if shifted.get("minimum_confirmed_duration_seconds") is not None:
            candidates.append(float(shifted["minimum_confirmed_duration_seconds"]))
        if existing.minimum_confirmed_duration_seconds is not None:
            candidates.append(existing.minimum_confirmed_duration_seconds)
        existing.minimum_confirmed_duration_seconds = round(max(candidates), 3)
        existing.last_seen_seconds = max(existing.last_seen_seconds, segment_end_global)

    def _close_open(self, key: Any, end_seconds: float | None) -> None:
        existing = self._open.pop(key, None)
        if existing is None:
            return
        self._closed.append(
            _finalized_incident_dict(
                person_id=existing.person_id,
                violated_items=existing.violated_items,
                start_seconds=existing.start_seconds,
                end_seconds=end_seconds,
                minimum_confirmed_duration_seconds=existing.minimum_confirmed_duration_seconds,
                confidence=existing.confidence,
                action_sequence=existing.action_sequence,
                evidence=existing.evidence,
            )
        )

    def _expire_stale(self, now_global: float, exclude: set[Any]) -> None:
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
                violated_items=incident.violated_items,
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
        key_to_id: dict[Any, str] = {}
        for position, incident in enumerate(all_incidents, start=1):
            incident_id = f"incident_{position:03d}"
            person_id = incident["person_id"]
            key = person_id if person_id is not None else "anonymous"
            key_to_id[key] = incident_id
            built.append(
                build_incident(
                    index=position,
                    ppe_items=incident["violated_items"],
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
    violated_items: set[str] | list[str],
    start_seconds: float,
    end_seconds: float | None,
    minimum_confirmed_duration_seconds: float | None,
    confidence: float | None,
    action_sequence: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "person_id": person_id,
        "violated_items": sorted(violated_items),
        "start_seconds": start_seconds,
        "end_seconds": end_seconds,
        "minimum_confirmed_duration_seconds": minimum_confirmed_duration_seconds,
        "confidence": confidence,
        "action_sequence": action_sequence,
        "evidence": evidence,
    }
