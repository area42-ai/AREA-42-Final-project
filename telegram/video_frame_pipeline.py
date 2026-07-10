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


load_dotenv()

API_URL = os.getenv(
    "NVIDIA_API_URL",
    "https://integrate.api.nvidia.com/v1/chat/completions",
)

MODEL = os.getenv(
    "NVIDIA_MODEL",
    "meta/llama-3.2-11b-vision-instruct",
)

DEFAULT_SAMPLE_INTERVAL = 1.0
DEFAULT_CONFIRMATION_FRAMES = 2


PROMPT = """
Analyze this single frame from a workplace safety video.

Focus on the most clearly visible worker.

Check whether the worker is currently wearing a protective hard hat
on their head.

Important:
- A hard hat held in the person's hands does not count as being worn.
- A hard hat near the person does not count as being worn.
- Judge only what is visible in this frame.
- Do not infer what happened before or after this frame.

Return exactly one valid JSON object and no Markdown:

{
  "person_visible": true,
  "hard_hat_visible_on_head": false,
  "state": "violation",
  "violation": true,
  "confidence": "high",
  "evidence": "short factual explanation",
  "uncertainties": []
}

Rules:
- state must be one of: violation, compliant, uncertain.
- Use violation when the visible worker is clearly not wearing a hard hat.
- Use compliant when the visible worker is clearly wearing a hard hat.
- Use uncertain when the worker is not visible, the head is obscured,
  or the hard hat cannot be judged reliably.
- violation must be true only when state is violation.
- violation must be false when state is compliant or uncertain.
- confidence must be one of: high, medium, low.
- Do not invent objects, people or actions.
""".strip()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze a local workplace video for missing-hard-hat "
            "violations using a hosted NVIDIA vision model."
        )
    )

    parser.add_argument(
        "--video",
        required=True,
        help="Path to the local MP4 video.",
    )

    parser.add_argument(
        "--sample-interval",
        type=float,
        default=DEFAULT_SAMPLE_INTERVAL,
        help="Seconds between sampled frames. Default: 1.0",
    )

    parser.add_argument(
        "--confirmation-frames",
        type=int,
        default=DEFAULT_CONFIRMATION_FRAMES,
        help=(
            "Number of consecutive classifications required to open "
            "or close an incident. Default: 2"
        ),
    )

    parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Optional output directory. "
            "Default: outputs/<video filename>"
        ),
    )

    return parser.parse_args()


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

    if start == -1 or end == -1:
        raise ValueError(
            "The model response does not contain a JSON object."
        )

    return json.loads(cleaned[start : end + 1])


def normalize_result(result: dict[str, Any]) -> dict[str, Any]:
    state = str(result.get("state", "uncertain")).lower().strip()

    if state not in {"violation", "compliant", "uncertain"}:
        state = "uncertain"

    confidence = str(
        result.get("confidence", "low")
    ).lower().strip()

    if confidence not in {"high", "medium", "low"}:
        confidence = "low"

    uncertainties = result.get("uncertainties", [])

    if not isinstance(uncertainties, list):
        uncertainties = [str(uncertainties)]

    hard_hat_value = result.get("hard_hat_visible_on_head")

    if state == "compliant":
        hard_hat_visible_on_head = True
    elif state == "violation":
        hard_hat_visible_on_head = False
    else:
        hard_hat_visible_on_head = (
            hard_hat_value
            if isinstance(hard_hat_value, bool)
            else None
        )

    return {
        "person_visible": bool(
            result.get("person_visible", False)
        ),
        "hard_hat_visible_on_head": hard_hat_visible_on_head,
        "state": state,
        "violation": state == "violation",
        "confidence": confidence,
        "evidence": str(result.get("evidence", "")).strip(),
        "uncertainties": uncertainties,
    }


def analyze_frame(
    frame_path: Path,
    api_key: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    image_base64 = base64.b64encode(
        frame_path.read_bytes()
    ).decode("utf-8")

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": PROMPT,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                "data:image/jpeg;base64,"
                                + image_base64
                            )
                        },
                    },
                ],
            }
        ],
        "temperature": 0.1,
        "max_tokens": 500,
        "stream": False,
    }

    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=payload,
        timeout=180,
    )

    if not response.ok:
        raise RuntimeError(
            f"NVIDIA API error {response.status_code}: "
            f"{response.text}"
        )

    raw_response = response.json()

    model_text = raw_response["choices"][0]["message"]["content"]

    parsed_result = extract_json(str(model_text))
    normalized_result = normalize_result(parsed_result)

    return normalized_result, raw_response


def copy_evidence_frame(
    source_path: str,
    evidence_dir: Path,
    destination_name: str,
) -> str:
    source = Path(source_path)
    destination = evidence_dir / destination_name

    shutil.copy2(source, destination)

    return str(destination)


def build_incidents(
    frame_results: list[dict[str, Any]],
    evidence_dir: Path,
    video_duration: float,
    confirmation_frames: int,
) -> list[dict[str, Any]]:
    incidents: list[dict[str, Any]] = []

    violation_streak: list[dict[str, Any]] = []
    compliant_streak: list[dict[str, Any]] = []

    active_incident: dict[str, Any] | None = None

    for record in frame_results:
        state = record.get("state", "uncertain")

        if active_incident is None:
            if state == "violation":
                violation_streak.append(record)

                if len(violation_streak) >= confirmation_frames:
                    first_violation = violation_streak[0]

                    active_incident = {
                        "start_time_seconds": (
                            first_violation["timestamp_seconds"]
                        ),
                        "start_frame_source": (
                            first_violation["frame_path"]
                        ),
                        "last_violation_frame_source": (
                            record["frame_path"]
                        ),
                    }

                    violation_streak = []

            else:
                # Opening requires consecutive violation results.
                violation_streak = []

        else:
            if state == "violation":
                active_incident[
                    "last_violation_frame_source"
                ] = record["frame_path"]

                compliant_streak = []

            elif state == "compliant":
                compliant_streak.append(record)

                if len(compliant_streak) >= confirmation_frames:
                    first_compliant = compliant_streak[0]

                    incident_number = len(incidents) + 1

                    start_evidence = copy_evidence_frame(
                        active_incident["start_frame_source"],
                        evidence_dir,
                        (
                            f"incident_{incident_number:03d}_"
                            "start_violation.jpg"
                        ),
                    )

                    end_evidence = copy_evidence_frame(
                        first_compliant["frame_path"],
                        evidence_dir,
                        (
                            f"incident_{incident_number:03d}_"
                            "end_compliant.jpg"
                        ),
                    )

                    start_time = float(
                        active_incident[
                            "start_time_seconds"
                        ]
                    )
                    end_time = float(
                        first_compliant[
                            "timestamp_seconds"
                        ]
                    )

                    incidents.append(
                        {
                            "incident_id": incident_number,
                            "type": "missing_hard_hat",
                            "status": "resolved",
                            "start_time_seconds": start_time,
                            "end_time_seconds": end_time,
                            "duration_seconds": round(
                                end_time - start_time,
                                2,
                            ),
                            "start_evidence_frame": start_evidence,
                            "end_evidence_frame": end_evidence,
                            "message": (
                                "The worker was observed without a "
                                "hard hat and was later observed "
                                "wearing it again."
                            ),
                        }
                    )

                    active_incident = None
                    compliant_streak = []
                    violation_streak = []

            else:
                # Uncertain does not close an active incident,
                # but it interrupts a compliant confirmation streak.
                compliant_streak = []

    if active_incident is not None:
        incident_number = len(incidents) + 1

        start_evidence = copy_evidence_frame(
            active_incident["start_frame_source"],
            evidence_dir,
            (
                f"incident_{incident_number:03d}_"
                "start_violation.jpg"
            ),
        )

        last_evidence = copy_evidence_frame(
            active_incident[
                "last_violation_frame_source"
            ],
            evidence_dir,
            (
                f"incident_{incident_number:03d}_"
                "last_seen_violation.jpg"
            ),
        )

        start_time = float(
            active_incident["start_time_seconds"]
        )

        incidents.append(
            {
                "incident_id": incident_number,
                "type": "missing_hard_hat",
                "status": "open_at_video_end",
                "start_time_seconds": start_time,
                "end_time_seconds": None,
                "observed_until_seconds": round(
                    video_duration,
                    2,
                ),
                "duration_seconds": round(
                    video_duration - start_time,
                    2,
                ),
                "start_evidence_frame": start_evidence,
                "end_evidence_frame": None,
                "last_seen_violation_frame": last_evidence,
                "message": (
                    "The worker was not observed wearing a hard hat "
                    "again before the video ended."
                ),
            }
        )

    return incidents


def main() -> None:
    args = parse_arguments()

    api_key = os.getenv("NVIDIA_API_KEY")

    if not api_key:
        raise RuntimeError(
            "NVIDIA_API_KEY was not found. "
            "Create a local .env file."
        )

    video_path = Path(args.video)

    if not video_path.exists():
        raise FileNotFoundError(
            f"Video was not found: {video_path}"
        )

    if args.sample_interval <= 0:
        raise ValueError(
            "--sample-interval must be greater than zero."
        )

    if args.confirmation_frames < 1:
        raise ValueError(
            "--confirmation-frames must be at least 1."
        )

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else Path("outputs") / video_path.stem
    )

    frames_dir = output_dir / "frames"
    evidence_dir = output_dir / "evidence"

    frames_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    video = cv2.VideoCapture(str(video_path))

    if not video.isOpened():
        raise RuntimeError(
            f"Could not open video: {video_path}"
        )

    fps = video.get(cv2.CAP_PROP_FPS)
    frame_count = int(
        video.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    if fps <= 0:
        raise RuntimeError(
            "Could not determine the video FPS."
        )

    duration_seconds = frame_count / fps

    print(f"Video: {video_path}")
    print(f"Model: {MODEL}")
    print(f"Video FPS: {fps:.2f}")
    print(
        f"Video duration: {duration_seconds:.2f} seconds"
    )
    print(
        f"Sample interval: {args.sample_interval:.2f} seconds"
    )
    print()

    frame_results: list[dict[str, Any]] = []
    raw_responses: list[dict[str, Any]] = []

    timestamp = 0.0
    sample_number = 0

    while timestamp <= duration_seconds:
        video.set(
            cv2.CAP_PROP_POS_MSEC,
            timestamp * 1000,
        )

        success, frame = video.read()

        if not success:
            break

        frame_name = (
            f"frame_{sample_number:04d}_"
            f"{timestamp:.2f}s.jpg"
        )

        frame_path = frames_dir / frame_name

        cv2.imwrite(str(frame_path), frame)

        print(
            f"Analyzing frame at {timestamp:.2f} seconds..."
        )

        try:
            model_result, raw_response = analyze_frame(
                frame_path,
                api_key,
            )

            record = {
                "timestamp_seconds": round(timestamp, 2),
                "frame_path": str(frame_path),
                **model_result,
            }

            frame_results.append(record)

            raw_responses.append(
                {
                    "timestamp_seconds": round(
                        timestamp,
                        2,
                    ),
                    "response": raw_response,
                }
            )

            print(
                "  state:",
                record.get("state"),
                "| violation:",
                record.get("violation"),
                "| hard hat on head:",
                record.get(
                    "hard_hat_visible_on_head"
                ),
                "| confidence:",
                record.get("confidence"),
            )

        except Exception as error:
            frame_results.append(
                {
                    "timestamp_seconds": round(
                        timestamp,
                        2,
                    ),
                    "frame_path": str(frame_path),
                    "state": "uncertain",
                    "violation": False,
                    "error": str(error),
                }
            )

            print("  ERROR:", error)

        sample_number += 1
        timestamp += args.sample_interval

        # Avoid sending requests in an immediate burst.
        time.sleep(0.5)

    video.release()

    frame_results_path = (
        output_dir / "frame_results.json"
    )
    raw_responses_path = (
        output_dir / "raw_responses.json"
    )

    frame_results_path.write_text(
        json.dumps(
            frame_results,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    raw_responses_path.write_text(
        json.dumps(
            raw_responses,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    incidents = build_incidents(
        frame_results=frame_results,
        evidence_dir=evidence_dir,
        video_duration=duration_seconds,
        confirmation_frames=args.confirmation_frames,
    )

    incident_document = {
        "video": str(video_path),
        "model": MODEL,
        "video_duration_seconds": round(
            duration_seconds,
            2,
        ),
        "sample_interval_seconds": (
            args.sample_interval
        ),
        "confirmation_frames": (
            args.confirmation_frames
        ),
        "incident_count": len(incidents),
        "incidents": incidents,
    }

    incident_path = output_dir / "incident.json"

    incident_path.write_text(
        json.dumps(
            incident_document,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    if incidents:
        print("\nTriggering Telegram notification bot...")
        try:
            subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parent / "send_notification_bot.py"),
                    "--input",
                    str(incident_path),
                ],
                check=False,
            )
        except Exception as notify_err:
            print(f"Failed to run notification bot: {notify_err}")

    print()
    print("DONE")
    print(f"Frame results: {frame_results_path}")
    print(f"Incident result: {incident_path}")
    print(f"Evidence frames: {evidence_dir}")

    if incidents:
        for incident in incidents:
            print()
            print(
                f"Incident #{incident['incident_id']}: "
                f"{incident['status']}"
            )
            print(
                "  start:",
                incident["start_time_seconds"],
                "seconds",
            )
            print(
                "  end:",
                incident["end_time_seconds"],
            )
            print(
                "  duration:",
                incident["duration_seconds"],
                "seconds",
            )
    else:
        print()
        print("No confirmed hard-hat violation detected.")


if __name__ == "__main__":
    main()