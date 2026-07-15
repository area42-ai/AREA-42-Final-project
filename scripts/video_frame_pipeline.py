"""
AREA-42 Watch Out: direct Llama Vision PPE frame pipeline (source_pipeline: llama_direct).

Scope: full PPE set (hard_hat, safety_vest, safety_glasses, gloves), configurable
via --ppe-items.

The model performs neutral per-frame visual classification only. Python derives
violation/compliant semantics and runs an INDEPENDENT temporal state machine per
PPE item. Alert/notification decisions belong to a separate deterministic rule
engine.

Preserved robustness features: image resize/compression, retries with backoff,
separate connect/read timeouts, abort after consecutive technical errors,
checkpoints after each API response, explicit model-refusal handling, raw
HTTP/model diagnostics, sequential frame extraction, normalized_incident.json,
and unresolved-incident semantics.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import cv2
import requests
from dotenv import load_dotenv

if __package__:
    from .incident_contract import (
        PPE_ITEMS,
        STATUS_RESOLVED,
        STATUS_UNRESOLVED,
        build_envelope,
        build_incident,
        normalize_status,
        parse_ppe_items,
    )
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from incident_contract import (
        PPE_ITEMS,
        STATUS_RESOLVED,
        STATUS_UNRESOLVED,
        build_envelope,
        build_incident,
        normalize_status,
        parse_ppe_items,
    )


REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=REPO_ROOT / ".env")

DEFAULT_API_URL = os.getenv(
    "NVIDIA_API_URL",
    "https://integrate.api.nvidia.com/v1/chat/completions",
)
DEFAULT_MODEL = os.getenv(
    "NVIDIA_MODEL",
    "meta/llama-3.2-90b-vision-instruct",
)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
REFUSAL_PATTERNS = (
    "i'm not going to engage",
    "i am not going to engage",
    "i can't assist",
    "i cannot assist",
    "unable to assist",
    "cannot comply",
    "can't comply",
)

# Which body area must be visible for each PPE item to be judged.
PPE_BODY_AREA = {
    "hard_hat": ("head", "the head is not visible"),
    "safety_vest": ("torso", "the torso is not visible"),
    "safety_glasses": ("eyes", "the face/eyes are not visible"),
    "gloves": ("hands", "the hands are not visible"),
}
PPE_LABELS = {
    "hard_hat": "a protective hard hat worn on the head",
    "safety_vest": "a high-visibility safety vest on the torso",
    "safety_glasses": "safety glasses over the eyes",
    "gloves": "protective gloves on the hands",
}


def build_prompt(ppe_items: list[str]) -> str:
    example_entries = []
    rule_lines = []
    for item in ppe_items:
        example_entries.append(
            f'    "{item}": {{\n'
            f'      "status": "unknown",\n'
            f'      "confidence": "low",\n'
            f'      "evidence": "short visual observation"\n'
            f'    }}'
        )
        _, invisible_phrase = PPE_BODY_AREA[item]
        rule_lines.append(
            f"- {item}: if {invisible_phrase}, status must be unknown."
        )

    example_block = "{\n  \"person_visible\": true,\n  \"hand_visible\": true,\n  \"ppe\": {\n" + ",\n".join(
        example_entries
    ) + "\n  }\n}"
    rules_block = "\n".join(rule_lines)

    return f"""
You are performing a neutral visual classification task on one image.

Inspect only the most clearly visible person. Do not identify the person, infer
intent, or use information outside the image. Report only what pixels show.

Return exactly one JSON object and no Markdown:
{example_block}

Rules:
- For each PPE item, status must be exactly one of: present, missing, unknown,
  not_applicable.
- present means the item is clearly worn correctly.
- missing means the relevant body area is visible and the item is not worn.
- unknown means the item cannot be judged reliably.
- hand_visible must be true only if at least one actual hand is visibly detected.
- If hand_visible is false, gloves status must be unknown, never missing.
{rules_block}
- confidence must be exactly one of: high, medium, low.
- evidence must be one short factual sentence about visible pixels only.
- Report only these PPE items: {", ".join(ppe_items)}.
""".strip()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze sampled video frames for missing-PPE incidents using an "
            "NVIDIA-hosted Llama Vision model."
        )
    )
    parser.add_argument("--video", required=True, help="Path to an MP4 video.")
    parser.add_argument(
        "--ppe-items",
        default=None,
        help=f"Comma-separated PPE scope. Default: {','.join(PPE_ITEMS)}.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model name. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help="NVIDIA chat-completions endpoint.",
    )
    parser.add_argument(
        "--sample-interval",
        type=float,
        default=1.0,
        help="Seconds between sampled frames. Default: 1.0",
    )
    parser.add_argument(
        "--confirmation-frames",
        type=int,
        default=2,
        help="Consecutive results required to open/close an incident.",
    )
    parser.add_argument(
        "--start-seconds",
        type=float,
        default=0.0,
        help="Start analysis at this timestamp. Default: 0.",
    )
    parser.add_argument(
        "--end-seconds",
        type=float,
        default=None,
        help="Stop analysis at this timestamp. Default: video end.",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Maximum number of sampled frames/API calls.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Default: outputs/<video_stem>",
    )
    parser.add_argument(
        "--connect-timeout",
        type=float,
        default=10.0,
        help="HTTP connection timeout in seconds. Default: 10.",
    )
    parser.add_argument(
        "--read-timeout",
        type=float,
        default=60.0,
        help="HTTP response timeout in seconds. Default: 60.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=1,
        help="Retries for timeout/429/5xx failures. Default: 1.",
    )
    parser.add_argument(
        "--retry-backoff",
        type=float,
        default=2.0,
        help="Base exponential retry delay. Default: 2 seconds.",
    )
    parser.add_argument(
        "--abort-after-consecutive-errors",
        type=int,
        default=3,
        help=(
            "Abort after this many consecutive technical errors. "
            "Use 0 to disable. Default: 3."
        ),
    )
    parser.add_argument(
        "--request-delay",
        type=float,
        default=0.5,
        help="Delay between completed frame requests. Default: 0.5.",
    )
    parser.add_argument(
        "--max-image-dimension",
        type=int,
        default=768,
        help="Resize the longest image side before upload. Default: 768.",
    )
    parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=78,
        help="Initial JPEG quality for API frames. Default: 78.",
    )
    parser.add_argument(
        "--max-image-bytes",
        type=int,
        default=175_000,
        help="Target maximum JPEG size sent inline. Default: 175000.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=320,
        help="Maximum generated tokens per frame. Default: 320.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract sampled frames and write metadata without API calls.",
    )
    parser.add_argument(
        "--camera-name",
        default=os.getenv("CAMERA_NAME", "Kamera-1"),
        help="Telegram bildiriminde gösterilecek kamera adı/numarası.",
    )
    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> None:
    if args.sample_interval <= 0:
        raise ValueError("--sample-interval must be greater than zero.")
    if args.confirmation_frames < 1:
        raise ValueError("--confirmation-frames must be at least 1.")
    if args.start_seconds < 0:
        raise ValueError("--start-seconds cannot be negative.")
    if args.end_seconds is not None and args.end_seconds < args.start_seconds:
        raise ValueError("--end-seconds cannot be before --start-seconds.")
    if args.max_frames is not None and args.max_frames < 1:
        raise ValueError("--max-frames must be at least 1.")
    if args.connect_timeout <= 0 or args.read_timeout <= 0:
        raise ValueError("HTTP timeouts must be greater than zero.")
    if args.max_retries < 0:
        raise ValueError("--max-retries cannot be negative.")
    if args.abort_after_consecutive_errors < 0:
        raise ValueError("--abort-after-consecutive-errors cannot be negative.")
    if args.max_image_dimension < 128:
        raise ValueError("--max-image-dimension must be at least 128.")
    if not 30 <= args.jpeg_quality <= 95:
        raise ValueError("--jpeg-quality must be between 30 and 95.")
    if args.max_image_bytes < 20_000:
        raise ValueError("--max-image-bytes is implausibly small.")
    if args.max_tokens < 32:
        raise ValueError("--max-tokens must be at least 32.")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary_path.replace(path)


def extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("The model response does not contain a JSON object.")
    parsed = json.loads(cleaned[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("The model response JSON is not an object.")
    return parsed


def is_refusal(text: str) -> bool:
    lowered = text.casefold()
    return any(pattern in lowered for pattern in REFUSAL_PATTERNS)


def normalize_frame(
    result: dict[str, Any],
    ppe_items: list[str],
) -> dict[str, Any]:
    """Normalize a per-frame model response into per-item PPE statuses.

    Any item the model omitted, or whose body area is not visible, becomes
    'unknown'. Python (not the model) later maps 'missing' onto violations.
    """
    raw_ppe = result.get("ppe")
    if not isinstance(raw_ppe, dict):
        raw_ppe = {}

    person_visible_value = result.get("person_visible")
    person_visible = (
        person_visible_value
        if isinstance(person_visible_value, bool)
        else None
    )

    # The gloves rule is deliberately deterministic: model output saying
    # "gloves missing" is not actionable unless a hand object is also visible.
    hand_visible_value = result.get("hand_visible")
    if isinstance(hand_visible_value, bool):
        hand_visible = hand_visible_value
    else:
        detections = result.get("detections", result.get("objects", []))
        if not isinstance(detections, list):
            detections = []
        labels = []
        for detection in detections:
            if isinstance(detection, dict):
                labels.append(
                    str(
                        detection.get("label")
                        or detection.get("class")
                        or detection.get("name")
                        or ""
                    ).casefold()
                )
            else:
                labels.append(str(detection).casefold())
        hand_visible = any(label in {"hand", "hands", "el"} for label in labels)

    ppe: dict[str, dict[str, Any]] = {}
    for item in ppe_items:
        entry = raw_ppe.get(item)
        if not isinstance(entry, dict):
            entry = {}
        status = normalize_status(entry.get("status", "unknown"))
        if item == "gloves" and not hand_visible:
            status = "unknown"
        confidence = str(entry.get("confidence", "low")).lower().strip()
        if confidence not in {"high", "medium", "low"}:
            confidence = "low"
        evidence = str(entry.get("evidence", "")).strip()
        ppe[item] = {
            "status": status,
            "confidence": confidence,
            "evidence": evidence,
        }

    return {
        "person_visible": person_visible,
        "hand_visible": hand_visible,
        "ppe": ppe,
    }


def resize_frame(frame: Any, max_dimension: int) -> Any:
    height, width = frame.shape[:2]
    longest_side = max(height, width)
    if longest_side <= max_dimension:
        return frame
    scale = max_dimension / float(longest_side)
    target_width = max(1, round(width * scale))
    target_height = max(1, round(height * scale))
    return cv2.resize(
        frame,
        (target_width, target_height),
        interpolation=cv2.INTER_AREA,
    )


def encode_frame_for_api(
    frame: Any,
    max_dimension: int,
    initial_quality: int,
    max_bytes: int,
) -> tuple[bytes, dict[str, Any]]:
    working_frame = resize_frame(frame, max_dimension)
    quality = initial_quality
    while True:
        success, encoded = cv2.imencode(
            ".jpg",
            working_frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), quality],
        )
        if not success:
            raise RuntimeError("OpenCV could not encode a sampled frame.")
        image_bytes = encoded.tobytes()
        if len(image_bytes) <= max_bytes or quality <= 45:
            break
        quality -= 7

    height, width = working_frame.shape[:2]
    metadata = {
        "api_image_width": width,
        "api_image_height": height,
        "api_image_bytes": len(image_bytes),
        "api_jpeg_quality": quality,
    }
    return image_bytes, metadata


def retry_delay_seconds(
    response: requests.Response | None,
    base_backoff: float,
    attempt_index: int,
) -> float:
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass
    return base_backoff * (2 ** attempt_index)


def extract_model_text(raw_response: dict[str, Any]) -> str:
    try:
        content = raw_response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError(
            "API response is missing choices[0].message.content."
        ) from error
    if content is None:
        raise ValueError("Model content is null.")
    return str(content)


def analyze_frame(
    *,
    session: requests.Session,
    image_bytes: bytes,
    api_key: str,
    api_url: str,
    model: str,
    prompt: str,
    ppe_items: list[str],
    connect_timeout: float,
    read_timeout: float,
    max_retries: int,
    retry_backoff: float,
    max_tokens: int,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    image_base64 = base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/jpeg;base64," + image_base64,
                        },
                    },
                ],
            }
        ],
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "stream": False,
        "seed": 42,
    }

    diagnostic: dict[str, Any] = {
        "analysis_status": "technical_error",
        "attempts": [],
        "raw_response": None,
        "raw_body": None,
        "model_text": None,
        "parse_error": None,
        "error_type": None,
        "error_message": None,
    }

    total_attempts = max_retries + 1

    for attempt in range(total_attempts):
        started = time.monotonic()
        response: requests.Response | None = None
        attempt_record: dict[str, Any] = {
            "attempt": attempt + 1,
            "elapsed_seconds": None,
            "status_code": None,
            "error_type": None,
            "error_message": None,
        }

        try:
            response = session.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payload,
                timeout=(connect_timeout, read_timeout),
            )
            attempt_record["elapsed_seconds"] = round(
                time.monotonic() - started,
                3,
            )
            attempt_record["status_code"] = response.status_code

            if response.status_code in RETRYABLE_STATUS_CODES:
                attempt_record["error_type"] = "retryable_http_error"
                attempt_record["error_message"] = response.text[:1000]
                diagnostic["attempts"].append(attempt_record)
                if attempt < max_retries:
                    delay = retry_delay_seconds(
                        response,
                        retry_backoff,
                        attempt,
                    )
                    print(
                        f"  transient HTTP {response.status_code}; "
                        f"retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)
                    continue

            if not response.ok:
                diagnostic.update(
                    {
                        "analysis_status": "http_error",
                        "raw_body": response.text[:20_000],
                        "error_type": "http_error",
                        "error_message": (
                            f"NVIDIA API error {response.status_code}: "
                            f"{response.text[:1000]}"
                        ),
                    }
                )
                diagnostic["attempts"].append(attempt_record)
                return None, diagnostic

            diagnostic["raw_body"] = response.text[:100_000]

            try:
                raw_response = response.json()
            except ValueError as error:
                diagnostic.update(
                    {
                        "analysis_status": "response_error",
                        "error_type": "non_json_http_body",
                        "error_message": str(error),
                    }
                )
                diagnostic["attempts"].append(attempt_record)
                return None, diagnostic

            diagnostic["raw_response"] = raw_response

            try:
                model_text = extract_model_text(raw_response)
            except ValueError as error:
                diagnostic.update(
                    {
                        "analysis_status": "response_error",
                        "error_type": "missing_model_content",
                        "error_message": str(error),
                    }
                )
                diagnostic["attempts"].append(attempt_record)
                return None, diagnostic

            diagnostic["model_text"] = model_text

            if is_refusal(model_text):
                diagnostic.update(
                    {
                        "analysis_status": "model_refusal",
                        "error_type": "model_refusal",
                        "error_message": model_text,
                    }
                )
                diagnostic["attempts"].append(attempt_record)
                return None, diagnostic

            try:
                parsed_result = extract_json(model_text)
                normalized_result = normalize_frame(parsed_result, ppe_items)
            except (ValueError, json.JSONDecodeError) as error:
                diagnostic.update(
                    {
                        "analysis_status": "parse_error",
                        "parse_error": str(error),
                        "error_type": "parse_error",
                        "error_message": str(error),
                    }
                )
                diagnostic["attempts"].append(attempt_record)
                return None, diagnostic

            diagnostic["analysis_status"] = "success"
            diagnostic["attempts"].append(attempt_record)
            return normalized_result, diagnostic

        except (requests.Timeout, requests.ConnectionError) as error:
            attempt_record["elapsed_seconds"] = round(
                time.monotonic() - started,
                3,
            )
            attempt_record["error_type"] = type(error).__name__
            attempt_record["error_message"] = str(error)
            diagnostic["attempts"].append(attempt_record)

            if attempt < max_retries:
                delay = retry_delay_seconds(
                    response,
                    retry_backoff,
                    attempt,
                )
                print(
                    f"  {type(error).__name__}; "
                    f"retrying in {delay:.1f}s"
                )
                time.sleep(delay)
                continue

            diagnostic.update(
                {
                    "analysis_status": "network_error",
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                }
            )
            return None, diagnostic

        except requests.RequestException as error:
            attempt_record["elapsed_seconds"] = round(
                time.monotonic() - started,
                3,
            )
            attempt_record["error_type"] = type(error).__name__
            attempt_record["error_message"] = str(error)
            diagnostic["attempts"].append(attempt_record)
            diagnostic.update(
                {
                    "analysis_status": "network_error",
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                }
            )
            return None, diagnostic

    diagnostic["error_type"] = "unreachable_retry_state"
    diagnostic["error_message"] = "Request retry loop ended unexpectedly."
    return None, diagnostic


def generate_sample_plan(
    *,
    fps: float,
    frame_count: int,
    duration_seconds: float,
    start_seconds: float,
    end_seconds: float | None,
    interval_seconds: float,
    max_frames: int | None,
) -> list[tuple[int, float]]:
    last_frame_time = max(0.0, (frame_count - 1) / fps)
    effective_end = min(
        last_frame_time,
        duration_seconds if end_seconds is None else end_seconds,
    )
    if start_seconds > effective_end:
        return []

    plan: list[tuple[int, float]] = []
    seen_indices: set[int] = set()
    timestamp = start_seconds

    while timestamp <= effective_end + 1e-9:
        frame_index = min(
            frame_count - 1,
            max(0, round(timestamp * fps)),
        )
        if frame_index not in seen_indices:
            actual_timestamp = frame_index / fps
            plan.append((frame_index, actual_timestamp))
            seen_indices.add(frame_index)
        if max_frames is not None and len(plan) >= max_frames:
            break
        timestamp += interval_seconds

    return plan


def extract_frames_sequentially(
    video_path: Path,
    sample_plan: list[tuple[int, float]],
) -> list[tuple[int, float, Any]]:
    if not sample_plan:
        return []

    targets = {frame_index: timestamp for frame_index, timestamp in sample_plan}
    last_target = max(targets)
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    extracted: list[tuple[int, float, Any]] = []
    frame_index = 0
    try:
        while frame_index <= last_target:
            success, frame = capture.read()
            if not success:
                break
            if frame_index in targets:
                extracted.append(
                    (frame_index, targets[frame_index], frame.copy())
                )
            frame_index += 1
    finally:
        capture.release()

    return extracted


def confidence_to_number(value: str) -> float:
    return {"high": 0.9, "medium": 0.6, "low": 0.3}.get(value, 0.3)


def copy_evidence_frame(
    source_path: str,
    evidence_dir: Path,
    destination_name: str,
) -> str:
    source = Path(source_path)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    destination = evidence_dir / destination_name
    shutil.copy2(source, destination)
    return str(destination)


def item_signal(record: dict[str, Any], item: str) -> str:
    """Map a frame record to this item's temporal signal.

    Non-success frames (refusal/timeout/http/parse) and unknown/not_applicable
    statuses become 'uncertain': they never close an active incident and, before
    an incident opens, they interrupt a missing streak.
    """
    if record.get("analysis_status") != "success":
        return "uncertain"
    entry = record.get("ppe", {}).get(item, {})
    status = entry.get("status", "unknown")
    if status == "missing":
        return "violation"
    if status == "present":
        return "compliant"
    return "uncertain"


def item_confidence(record: dict[str, Any], item: str) -> float:
    entry = record.get("ppe", {}).get(item, {})
    return confidence_to_number(entry.get("confidence", "low"))


def build_item_incidents(
    *,
    item: str,
    frame_results: list[dict[str, Any]],
    evidence_dir: Path,
    confirmation_frames: int,
) -> list[dict[str, Any]]:
    """Independent temporal state machine for a single PPE item."""
    incidents: list[dict[str, Any]] = []
    violation_streak: list[dict[str, Any]] = []
    compliant_streak: list[dict[str, Any]] = []
    active: dict[str, Any] | None = None

    def make_evidence_name(local_number: int, suffix: str) -> str:
        return f"{item}_incident_{local_number:03d}_{suffix}.jpg"

    for record in frame_results:
        signal = item_signal(record, item)

        if active is None:
            if signal == "violation":
                violation_streak.append(record)
                if len(violation_streak) >= confirmation_frames:
                    first = violation_streak[0]
                    active = {
                        "start_time_seconds": first["timestamp_seconds"],
                        "start_frame_source": first["frame_path"],
                        "last_violation_time_seconds": record[
                            "timestamp_seconds"
                        ],
                        "last_violation_frame_source": record["frame_path"],
                        "confidence_values": [
                            item_confidence(frame, item)
                            for frame in violation_streak
                        ],
                    }
                    violation_streak = []
            else:
                violation_streak = []
            continue

        if signal == "violation":
            active["last_violation_time_seconds"] = record["timestamp_seconds"]
            active["last_violation_frame_source"] = record["frame_path"]
            active["confidence_values"].append(item_confidence(record, item))
            compliant_streak = []
        elif signal == "compliant":
            compliant_streak.append(record)
            if len(compliant_streak) >= confirmation_frames:
                first_compliant = compliant_streak[0]
                local_number = len(incidents) + 1
                start_time = float(active["start_time_seconds"])
                end_time = float(first_compliant["timestamp_seconds"])
                start_evidence = copy_evidence_frame(
                    active["start_frame_source"],
                    evidence_dir,
                    make_evidence_name(local_number, "start_violation"),
                )
                end_evidence = copy_evidence_frame(
                    first_compliant["frame_path"],
                    evidence_dir,
                    make_evidence_name(local_number, "end_compliant"),
                )
                confidence = round(
                    sum(active["confidence_values"])
                    / len(active["confidence_values"]),
                    3,
                )
                incidents.append(
                    {
                        "ppe_item": item,
                        "status": STATUS_RESOLVED,
                        "start_seconds": start_time,
                        "end_seconds": end_time,
                        "minimum_confirmed_duration_seconds": round(
                            float(active["last_violation_time_seconds"])
                            - start_time,
                            3,
                        ),
                        "confidence": confidence,
                        "evidence": [
                            {
                                "kind": "start_violation",
                                "timestamp_seconds": round(start_time, 3),
                                "frame_path": start_evidence,
                            },
                            {
                                "kind": "end_compliant",
                                "timestamp_seconds": round(end_time, 3),
                                "frame_path": end_evidence,
                            },
                        ],
                    }
                )
                active = None
                compliant_streak = []
                violation_streak = []
        else:
            compliant_streak = []

    if active is not None:
        local_number = len(incidents) + 1
        start_time = float(active["start_time_seconds"])
        last_time = float(active["last_violation_time_seconds"])
        start_evidence = copy_evidence_frame(
            active["start_frame_source"],
            evidence_dir,
            make_evidence_name(local_number, "start_violation"),
        )
        last_evidence = copy_evidence_frame(
            active["last_violation_frame_source"],
            evidence_dir,
            make_evidence_name(local_number, "last_seen_violation"),
        )
        confidence = round(
            sum(active["confidence_values"])
            / len(active["confidence_values"]),
            3,
        )
        incidents.append(
            {
                "ppe_item": item,
                "status": STATUS_UNRESOLVED,
                "start_seconds": start_time,
                "end_seconds": None,
                "minimum_confirmed_duration_seconds": round(
                    last_time - start_time,
                    3,
                ),
                "confidence": confidence,
                "evidence": [
                    {
                        "kind": "start_violation",
                        "timestamp_seconds": round(start_time, 3),
                        "frame_path": start_evidence,
                    },
                    {
                        "kind": "last_seen_violation",
                        "timestamp_seconds": round(last_time, 3),
                        "frame_path": last_evidence,
                    },
                ],
            }
        )

    return incidents


def build_all_incidents(
    *,
    frame_results: list[dict[str, Any]],
    evidence_dir: Path,
    confirmation_frames: int,
    ppe_items: list[str],
) -> list[dict[str, Any]]:
    """Run one independent state machine per PPE item, ordered by start time."""
    all_incidents: list[dict[str, Any]] = []
    for item in ppe_items:
        all_incidents.extend(
            build_item_incidents(
                item=item,
                frame_results=frame_results,
                evidence_dir=evidence_dir,
                confirmation_frames=confirmation_frames,
            )
        )
    all_incidents.sort(key=lambda incident: incident["start_seconds"])
    return all_incidents


def build_quality(
    frame_results: list[dict[str, Any]],
    planned_frame_count: int,
) -> dict[str, Any]:
    counts: dict[str, int] = {}
    warnings: list[str] = []
    for record in frame_results:
        status = str(record.get("analysis_status", "unknown"))
        counts[status] = counts.get(status, 0) + 1

    failure_count = sum(
        count for status, count in counts.items() if status != "success"
    )
    if counts.get("model_refusal", 0):
        warnings.append(
            f"{counts['model_refusal']} frame(s) were refused by the model."
        )
    if counts.get("network_error", 0):
        warnings.append(
            f"{counts['network_error']} frame(s) failed due to network timeout/error."
        )
    if counts.get("http_error", 0):
        warnings.append(
            f"{counts['http_error']} frame(s) failed with an HTTP error."
        )
    if counts.get("parse_error", 0):
        warnings.append(
            f"{counts['parse_error']} frame(s) returned unparseable output."
        )
    if len(frame_results) < planned_frame_count:
        warnings.append(
            "The run stopped before all planned frames were analyzed."
        )

    return {
        "parse_success": failure_count == 0
        and len(frame_results) == planned_frame_count,
        "planned_frames": planned_frame_count,
        "analyzed_frames": len(frame_results),
        "status_counts": counts,
        "warnings": warnings,
    }


def build_normalized_document(
    *,
    video_path: Path,
    model: str,
    ppe_items: list[str],
    incidents: list[dict[str, Any]],
    quality: dict[str, Any],
) -> dict[str, Any]:
    normalized_incidents: list[dict[str, Any]] = []

    for position, incident in enumerate(incidents, start=1):
        item = incident["ppe_item"]
        actions = [
            {
                "event": "ppe_absence_confirmed",
                "ppe_item": item,
                "timestamp_seconds": incident["start_seconds"],
                "description": f"{item} absence was confirmed.",
            }
        ]
        if incident.get("end_seconds") is not None:
            actions.append(
                {
                    "event": "ppe_presence_confirmed",
                    "ppe_item": item,
                    "timestamp_seconds": incident["end_seconds"],
                    "description": f"{item} presence was confirmed.",
                }
            )

        normalized_incidents.append(
            build_incident(
                index=position,
                ppe_item=item,
                start_seconds=incident["start_seconds"],
                end_seconds=incident["end_seconds"],
                status=incident["status"],
                minimum_confirmed_duration_seconds=incident.get(
                    "minimum_confirmed_duration_seconds"
                ),
                confidence=incident.get("confidence"),
                action_sequence=actions,
                evidence=incident.get("evidence", []),
            )
        )

    if normalized_incidents:
        violated = sorted({inc["violated_items"][0] for inc in normalized_incidents})
        summary = (
            f"Detected {len(normalized_incidents)} PPE incident(s) "
            f"across: {', '.join(violated)}."
        )
    else:
        summary = "No confirmed PPE incident was detected."

    return build_envelope(
        video_id=video_path.stem,
        source_pipeline="llama_direct",
        models=[model],
        analysis_scope=ppe_items,
        incidents=normalized_incidents,
        summary=summary,
        quality=quality,
    )


def clean_known_outputs(output_dir: Path) -> None:
    for directory_name in ("frames", "evidence"):
        target = output_dir / directory_name
        if target.exists():
            shutil.rmtree(target)
    for filename in (
        "frame_results.json",
        "raw_responses.json",
        "incident.json",
        "normalized_incident.json",
        "run_config.json",
    ):
        target = output_dir / filename
        if target.exists():
            target.unlink()


def main() -> None:
    args = parse_arguments()
    validate_arguments(args)
    ppe_items = parse_ppe_items(args.ppe_items)
    prompt = build_prompt(ppe_items)

    api_key = os.getenv("NVIDIA_API_KEY")
    if not args.dry_run and not api_key:
        raise RuntimeError(
            "NVIDIA_API_KEY was not found in the project .env file."
        )

    video_path = Path(args.video)
    if not video_path.exists():
        raise FileNotFoundError(f"Video was not found: {video_path}")

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    capture.release()

    if fps <= 0 or frame_count <= 0:
        raise RuntimeError("Could not determine video FPS/frame count.")

    duration_seconds = frame_count / fps
    sample_plan = generate_sample_plan(
        fps=fps,
        frame_count=frame_count,
        duration_seconds=duration_seconds,
        start_seconds=args.start_seconds,
        end_seconds=args.end_seconds,
        interval_seconds=args.sample_interval,
        max_frames=args.max_frames,
    )
    if not sample_plan:
        raise RuntimeError("The requested time range produced no sample frames.")

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else Path("outputs") / video_path.stem
    )
    clean_known_outputs(output_dir)
    frames_dir = output_dir / "frames"
    evidence_dir = output_dir / "evidence"
    frames_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    frame_results_path = output_dir / "frame_results.json"
    raw_responses_path = output_dir / "raw_responses.json"
    incident_path = output_dir / "incident.json"
    normalized_path = output_dir / "normalized_incident.json"

    run_config = {
        "video": str(video_path),
        "model": args.model,
        "api_url": args.api_url,
        "analysis_scope": ppe_items,
        "video_fps": fps,
        "video_frame_count": frame_count,
        "video_duration_seconds": round(duration_seconds, 3),
        "sample_interval_seconds": args.sample_interval,
        "confirmation_frames": args.confirmation_frames,
        "start_seconds": args.start_seconds,
        "end_seconds": args.end_seconds,
        "max_frames": args.max_frames,
        "connect_timeout": args.connect_timeout,
        "read_timeout": args.read_timeout,
        "max_retries": args.max_retries,
        "max_image_dimension": args.max_image_dimension,
        "max_image_bytes": args.max_image_bytes,
        "planned_samples": [
            {
                "frame_index": frame_index,
                "timestamp_seconds": round(timestamp, 3),
            }
            for frame_index, timestamp in sample_plan
        ],
        "dry_run": args.dry_run,
    }
    write_json(output_dir / "run_config.json", run_config)

    print(f"Video: {video_path}")
    print(f"Model: {args.model}")
    print(f"PPE scope: {', '.join(ppe_items)}")
    print(f"FPS: {fps:.3f}")
    print(f"Duration: {duration_seconds:.2f}s")
    print(f"Planned API calls: {len(sample_plan)}")
    print(
        "Timeouts: "
        f"connect={args.connect_timeout:.0f}s, "
        f"read={args.read_timeout:.0f}s"
    )
    print()

    extracted_frames = extract_frames_sequentially(video_path, sample_plan)
    if len(extracted_frames) != len(sample_plan):
        print(
            f"WARNING: extracted {len(extracted_frames)} of "
            f"{len(sample_plan)} planned frames."
        )

    frame_results: list[dict[str, Any]] = []
    raw_responses: list[dict[str, Any]] = []
    consecutive_technical_errors = 0

    with requests.Session() as session:
        for sample_number, (
            frame_index,
            timestamp,
            frame,
        ) in enumerate(extracted_frames):
            image_bytes, image_metadata = encode_frame_for_api(
                frame,
                max_dimension=args.max_image_dimension,
                initial_quality=args.jpeg_quality,
                max_bytes=args.max_image_bytes,
            )
            frame_name = (
                f"frame_{sample_number:04d}_"
                f"{timestamp:.3f}s.jpg"
            )
            frame_path = frames_dir / frame_name
            frame_path.write_bytes(image_bytes)

            print(
                f"[{sample_number + 1}/{len(sample_plan)}] "
                f"Analyzing {timestamp:.2f}s "
                f"({image_metadata['api_image_width']}x"
                f"{image_metadata['api_image_height']}, "
                f"{image_metadata['api_image_bytes'] / 1024:.1f} KiB)"
            )

            if args.dry_run:
                record = {
                    "timestamp_seconds": round(timestamp, 3),
                    "frame_index": frame_index,
                    "frame_path": str(frame_path),
                    "analysis_status": "dry_run",
                    "person_visible": None,
                    "ppe": {},
                    **image_metadata,
                }
                frame_results.append(record)
                write_json(frame_results_path, frame_results)
                continue

            result, diagnostic = analyze_frame(
                session=session,
                image_bytes=image_bytes,
                api_key=api_key,
                api_url=args.api_url,
                model=args.model,
                prompt=prompt,
                ppe_items=ppe_items,
                connect_timeout=args.connect_timeout,
                read_timeout=args.read_timeout,
                max_retries=args.max_retries,
                retry_backoff=args.retry_backoff,
                max_tokens=args.max_tokens,
            )

            analysis_status = diagnostic["analysis_status"]
            raw_record = {
                "timestamp_seconds": round(timestamp, 3),
                "frame_index": frame_index,
                "frame_path": str(frame_path),
                **image_metadata,
                **diagnostic,
            }
            raw_responses.append(raw_record)

            if result is None:
                record = {
                    "timestamp_seconds": round(timestamp, 3),
                    "frame_index": frame_index,
                    "frame_path": str(frame_path),
                    "analysis_status": analysis_status,
                    "person_visible": None,
                    "ppe": {},
                    "error_type": diagnostic.get("error_type"),
                    "error": diagnostic.get("error_message"),
                    **image_metadata,
                }
                frame_results.append(record)

                if analysis_status in {
                    "network_error",
                    "http_error",
                    "response_error",
                }:
                    consecutive_technical_errors += 1
                else:
                    # Refusal/parse failure is a model result, not API downtime.
                    consecutive_technical_errors = 0

                print(
                    f"  {analysis_status}: "
                    f"{diagnostic.get('error_message')}"
                )
            else:
                record = {
                    "timestamp_seconds": round(timestamp, 3),
                    "frame_index": frame_index,
                    "frame_path": str(frame_path),
                    "analysis_status": "success",
                    **image_metadata,
                    **result,
                }
                frame_results.append(record)
                consecutive_technical_errors = 0
                summary_bits = " | ".join(
                    f"{item}={result['ppe'][item]['status']}"
                    for item in ppe_items
                )
                print(f"  {summary_bits}")

            # Checkpoint after every API call so Ctrl+C/timeouts do not erase work.
            write_json(frame_results_path, frame_results)
            write_json(raw_responses_path, raw_responses)

            if (
                args.abort_after_consecutive_errors > 0
                and consecutive_technical_errors
                >= args.abort_after_consecutive_errors
            ):
                print(
                    "\nABORTING: "
                    f"{consecutive_technical_errors} consecutive technical "
                    "errors. Existing checkpoints were preserved."
                )
                break

            if args.request_delay > 0:
                time.sleep(args.request_delay)

    incidents = build_all_incidents(
        frame_results=frame_results,
        evidence_dir=evidence_dir,
        confirmation_frames=args.confirmation_frames,
        ppe_items=ppe_items,
    )
    quality = build_quality(frame_results, len(sample_plan))

    legacy_document = {
        "video": str(video_path),
        "model": args.model,
        "analysis_scope": ppe_items,
        "video_duration_seconds": round(duration_seconds, 3),
        "sample_interval_seconds": args.sample_interval,
        "confirmation_frames": args.confirmation_frames,
        "incident_count": len(incidents),
        "incidents": incidents,
        "quality": quality,
    }
    normalized_document = build_normalized_document(
        video_path=video_path,
        model=args.model,
        ppe_items=ppe_items,
        incidents=incidents,
        quality=quality,
    )

    write_json(frame_results_path, frame_results)
    write_json(raw_responses_path, raw_responses)
    write_json(incident_path, legacy_document)
    write_json(normalized_path, normalized_document)

    if incidents:
        print("\nTriggering Telegram notification bot...")
        try:
            subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parent / "send_notification_bot.py"),
                    "--input",
                    str(normalized_path),
                    "--camera-name",
                    args.camera_name,
                ],
                check=False,
            )
        except Exception as notify_err:
            print(f"Failed to run notification bot: {notify_err}")

    print("\nDONE")
    print(f"Frame results: {frame_results_path}")
    print(f"Raw diagnostics: {raw_responses_path}")
    print(f"Legacy incident: {incident_path}")
    print(f"Normalized incident: {normalized_path}")
    print(f"Quality: {json.dumps(quality, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
