"""Shared normalized Incident JSON contract for AREA-42 "Watch Out".

Every PPE pipeline (nemotron_gemma, gemma_direct, llama_direct, and a future
YOLO source) emits the SAME normalized document so the website/backend can work
against a single contract regardless of source.

Design rules encoded here:

* One incident refers to exactly one PPE item, so ``violated_items`` normally
  contains a single element. Two simultaneously missing items => two incidents.
* ``unknown`` is never treated as compliance and never as a violation.
* ``person_id`` stays ``None`` until real tracking exists.
* No notification/alert decisions live in the contract. Thresholds and alert
  policy belong to a separate deterministic rule engine.

Validation is pure Python (no heavy schema dependency).
"""

from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "1.0"

PPE_ITEMS: tuple[str, ...] = (
    "hard_hat",
    "safety_vest",
    "safety_glasses",
    "gloves",
)

PPE_STATUSES: tuple[str, ...] = (
    "present",
    "missing",
    "unknown",
    "not_applicable",
)

SOURCE_PIPELINES: tuple[str, ...] = (
    "nemotron_gemma",
    "gemma_direct",
    "llama_direct",
)

STATUS_RESOLVED = "resolved"
STATUS_UNRESOLVED = "unresolved_after_last_confirmed_violation"

# Maps loose model vocabulary onto the four allowed statuses. Anything unknown
# collapses to "unknown" so a vague answer is never read as compliance.
_STATUS_ALIASES: dict[str, str] = {
    "present": "present",
    "worn": "present",
    "compliant": "present",
    "wearing": "present",
    "on": "present",
    "yes": "present",
    "missing": "missing",
    "not_worn": "missing",
    "not worn": "missing",
    "absent": "missing",
    "removed": "missing",
    "violation": "missing",
    "no": "missing",
    "unknown": "unknown",
    "uncertain": "unknown",
    "not_visible": "unknown",
    "not visible": "unknown",
    "obscured": "unknown",
    "unclear": "unknown",
    "": "unknown",
    "not_applicable": "not_applicable",
    "na": "not_applicable",
    "n/a": "not_applicable",
}


def normalize_status(value: Any) -> str:
    """Coerce arbitrary model text into one of the four allowed statuses."""
    text = str(value).strip().lower()
    return _STATUS_ALIASES.get(text, "unknown")


def empty_status_map() -> dict[str, str]:
    """A full PPE map with every item set to ``unknown``."""
    return {item: "unknown" for item in PPE_ITEMS}


def parse_ppe_items(
    raw: str | None,
    default: tuple[str, ...] = PPE_ITEMS,
) -> list[str]:
    """Parse a comma-separated ``--ppe-items`` value.

    Empty/None yields the full default scope. Unknown items raise ValueError.
    Order is preserved and duplicates removed.
    """
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return list(default)

    items: list[str] = []
    for chunk in str(raw).split(","):
        candidate = chunk.strip().lower()
        if not candidate:
            continue
        if candidate not in PPE_ITEMS:
            raise ValueError(
                f"Unknown PPE item '{candidate}'. "
                f"Allowed: {', '.join(PPE_ITEMS)}."
            )
        if candidate not in items:
            items.append(candidate)

    return items or list(default)


def coerce_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def compute_duration(
    start_seconds: float | None,
    end_seconds: float | None,
) -> float | None:
    """Deterministic duration. ``None`` when the incident is unresolved."""
    if start_seconds is None or end_seconds is None:
        return None
    return round(float(end_seconds) - float(start_seconds), 3)


def default_quality(
    *,
    parse_success: bool = True,
    planned_frames: int | None = None,
    analyzed_frames: int | None = None,
    status_counts: dict[str, int] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "parse_success": parse_success,
        "planned_frames": planned_frames,
        "analyzed_frames": analyzed_frames,
        "status_counts": status_counts or {},
        "warnings": warnings or [],
    }


def build_incident(
    *,
    index: int,
    ppe_item: str,
    start_seconds: float | None,
    end_seconds: float | None,
    status: str,
    minimum_confirmed_duration_seconds: float | None = None,
    confidence: float | None = None,
    ppe_status: dict[str, str] | None = None,
    action_sequence: list[dict[str, Any]] | None = None,
    evidence: list[dict[str, Any]] | None = None,
    person_id: Any = None,
) -> dict[str, Any]:
    """Build one normalized incident for a single PPE item."""
    if ppe_item not in PPE_ITEMS:
        raise ValueError(f"Unknown PPE item '{ppe_item}'.")
    if status not in (STATUS_RESOLVED, STATUS_UNRESOLVED):
        raise ValueError(f"Unknown incident status '{status}'.")

    if ppe_status is None:
        ppe_status = empty_status_map()
        ppe_status[ppe_item] = "missing"

    start_value = (
        round(float(start_seconds), 3) if start_seconds is not None else None
    )
    end_value = (
        round(float(end_seconds), 3) if end_seconds is not None else None
    )
    minimum_value = (
        round(float(minimum_confirmed_duration_seconds), 3)
        if minimum_confirmed_duration_seconds is not None
        else None
    )

    return {
        "incident_id": f"incident_{index:03d}",
        "person_id": person_id,
        "status": status,
        "start_seconds": start_value,
        "end_seconds": end_value,
        "duration_seconds": compute_duration(start_value, end_value),
        "minimum_confirmed_duration_seconds": minimum_value,
        "violated_items": [ppe_item],
        "ppe_status": ppe_status,
        "confidence": confidence,
        "action_sequence": action_sequence or [],
        "evidence": evidence or [],
    }


def build_envelope(
    *,
    video_id: str,
    source_pipeline: str,
    models: list[str],
    analysis_scope: list[str],
    incidents: list[dict[str, Any]],
    summary: str = "",
    quality: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble the full normalized document. Deterministic, model-independent."""
    if source_pipeline not in SOURCE_PIPELINES:
        raise ValueError(
            f"Unknown source_pipeline '{source_pipeline}'. "
            f"Allowed: {', '.join(SOURCE_PIPELINES)}."
        )

    renumbered: list[dict[str, Any]] = []
    for position, incident in enumerate(incidents, start=1):
        incident = dict(incident)
        incident["incident_id"] = f"incident_{position:03d}"
        renumbered.append(incident)

    return {
        "schema_version": SCHEMA_VERSION,
        "video_id": video_id,
        "source_pipeline": source_pipeline,
        "models": list(models),
        "analysis_scope": list(analysis_scope),
        "incident_detected": len(renumbered) > 0,
        "incidents": renumbered,
        "summary": summary,
        "quality": quality if quality is not None else default_quality(),
    }


def normalized_incidents_from_model(
    raw_incidents: Any,
    analysis_scope: list[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Convert model-produced incident dicts into normalized incidents.

    Used by the text-based converters (Nemotron->Gemma and Gemma direct).
    Only ``missing`` items become incidents; ``unknown``/``present`` are not
    violations. Duration is recomputed in Python. ``end_seconds: null`` yields an
    unresolved incident with ``duration_seconds: null``.
    """
    warnings: list[str] = []
    incidents: list[dict[str, Any]] = []

    if not isinstance(raw_incidents, list):
        return incidents, ["'incidents' was not a list; treated as empty."]

    index = 0
    for position, raw in enumerate(raw_incidents, start=1):
        if not isinstance(raw, dict):
            warnings.append(f"incident #{position}: not an object; skipped.")
            continue

        ppe_item = str(raw.get("ppe_item", "")).strip().lower()
        if ppe_item not in analysis_scope:
            warnings.append(
                f"incident #{position}: ppe_item '{ppe_item}' outside scope; "
                "skipped."
            )
            continue

        status_value = normalize_status(raw.get("status", "missing"))
        if status_value != "missing":
            warnings.append(
                f"incident #{position}: {ppe_item} status '{status_value}' is "
                "not a violation; skipped."
            )
            continue

        start_seconds = coerce_float(raw.get("start_seconds"), None)
        if start_seconds is None:
            warnings.append(
                f"incident #{position}: missing numeric start_seconds; skipped."
            )
            continue

        end_seconds = coerce_float(raw.get("end_seconds"), None)
        minimum_confirmed = coerce_float(
            raw.get("minimum_confirmed_duration_seconds"), None
        )

        if end_seconds is None:
            incident_status = STATUS_UNRESOLVED
        else:
            incident_status = STATUS_RESOLVED
            if end_seconds < start_seconds:
                warnings.append(
                    f"incident #{position}: end before start; clamped."
                )
                end_seconds = start_seconds

        action_sequence = raw.get("action_sequence", [])
        if not isinstance(action_sequence, list):
            action_sequence = []
            warnings.append(
                f"incident #{position}: action_sequence not a list; reset."
            )

        worker_label = raw.get("worker")
        worker_label = (
            worker_label.strip()
            if isinstance(worker_label, str) and worker_label.strip()
            else None
        )

        index += 1
        incidents.append(
            build_incident(
                index=index,
                ppe_item=ppe_item,
                start_seconds=start_seconds,
                end_seconds=end_seconds,
                status=incident_status,
                minimum_confirmed_duration_seconds=minimum_confirmed,
                confidence=coerce_float(raw.get("confidence"), None),
                action_sequence=action_sequence,
                evidence=[],
                person_id=worker_label,
            )
        )

    return incidents, warnings


def validate_document(document: Any) -> list[str]:
    """Return a list of contract-violation messages. Empty list => valid."""
    errors: list[str] = []

    if not isinstance(document, dict):
        return ["Document is not a JSON object."]

    required_top = (
        "schema_version",
        "video_id",
        "source_pipeline",
        "models",
        "analysis_scope",
        "incident_detected",
        "incidents",
        "summary",
        "quality",
    )
    for field in required_top:
        if field not in document:
            errors.append(f"Missing top-level field: {field}.")

    if document.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            f"schema_version must be '{SCHEMA_VERSION}'."
        )

    if document.get("source_pipeline") not in SOURCE_PIPELINES:
        errors.append("source_pipeline is not one of the allowed values.")

    scope = document.get("analysis_scope")
    if not isinstance(scope, list) or not scope:
        errors.append("analysis_scope must be a non-empty list.")
        scope = []
    else:
        for item in scope:
            if item not in PPE_ITEMS:
                errors.append(f"analysis_scope contains unknown item '{item}'.")

    incidents = document.get("incidents")
    if not isinstance(incidents, list):
        errors.append("incidents must be a list.")
        incidents = []

    if isinstance(document.get("incident_detected"), bool):
        if document["incident_detected"] != (len(incidents) > 0):
            errors.append(
                "incident_detected does not match the incident count."
            )
    else:
        errors.append("incident_detected must be a boolean.")

    for position, incident in enumerate(incidents, start=1):
        errors.extend(_validate_incident(incident, position, scope))

    quality = document.get("quality")
    if not isinstance(quality, dict):
        errors.append("quality must be an object.")
    elif "parse_success" not in quality or not isinstance(
        quality.get("parse_success"), bool
    ):
        errors.append("quality.parse_success must be a boolean.")

    return errors


def _validate_incident(
    incident: Any,
    position: int,
    scope: list[str],
) -> list[str]:
    errors: list[str] = []
    prefix = f"incident #{position}"

    if not isinstance(incident, dict):
        return [f"{prefix}: not an object."]

    required = (
        "incident_id",
        "person_id",
        "status",
        "start_seconds",
        "end_seconds",
        "duration_seconds",
        "minimum_confirmed_duration_seconds",
        "violated_items",
        "ppe_status",
        "confidence",
        "action_sequence",
        "evidence",
    )
    for field in required:
        if field not in incident:
            errors.append(f"{prefix}: missing field '{field}'.")

    if incident.get("status") not in (STATUS_RESOLVED, STATUS_UNRESOLVED):
        errors.append(f"{prefix}: invalid status.")

    ppe_status = incident.get("ppe_status")
    if not isinstance(ppe_status, dict):
        errors.append(f"{prefix}: ppe_status must be an object.")
        ppe_status = {}
    else:
        if set(ppe_status.keys()) != set(PPE_ITEMS):
            errors.append(
                f"{prefix}: ppe_status must contain exactly {PPE_ITEMS}."
            )
        for key, value in ppe_status.items():
            if value not in PPE_STATUSES:
                errors.append(
                    f"{prefix}: ppe_status['{key}'] has invalid value "
                    f"'{value}'."
                )

    violated = incident.get("violated_items")
    if not isinstance(violated, list):
        errors.append(f"{prefix}: violated_items must be a list.")
    else:
        if len(violated) != 1:
            errors.append(
                f"{prefix}: one incident must reference exactly one PPE item."
            )
        for item in violated:
            if scope and item not in scope:
                errors.append(
                    f"{prefix}: violated item '{item}' outside analysis_scope."
                )
            # unknown is never a violation; a violated item must be 'missing'.
            if isinstance(ppe_status, dict) and ppe_status.get(item) != "missing":
                errors.append(
                    f"{prefix}: violated item '{item}' is not marked 'missing'."
                )

    start_seconds = incident.get("start_seconds")
    end_seconds = incident.get("end_seconds")
    duration = incident.get("duration_seconds")
    status = incident.get("status")

    if status == STATUS_UNRESOLVED:
        if end_seconds is not None:
            errors.append(f"{prefix}: unresolved incident must have end null.")
        if duration is not None:
            errors.append(
                f"{prefix}: unresolved incident must have duration null."
            )
    elif status == STATUS_RESOLVED:
        expected = compute_duration(start_seconds, end_seconds)
        if expected is None:
            errors.append(
                f"{prefix}: resolved incident needs numeric start/end."
            )
        elif duration is None or abs(float(duration) - expected) > 0.01:
            errors.append(
                f"{prefix}: duration_seconds ({duration}) must equal "
                f"end - start ({expected})."
            )

    return errors
