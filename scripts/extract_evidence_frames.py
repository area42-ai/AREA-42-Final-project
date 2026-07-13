r"""Extract evidence frames for a normalized_incident.json.

Incidents whose [start_seconds, end_seconds] intervals overlap share a single
extracted frame (taken from inside the overlap, with a small offset past the
overlap's start to avoid catching a transition/motion-blur moment) instead of
producing duplicate photos.

Usage:
  python scripts\extract_evidence_frames.py --video data\test\worker_removes_helmet.mp4 --incident-json outputs\live\camera_01\normalized_incident.json --output-dir outputs\live\camera_01\evidence
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import cv2


def merge_overlapping_incidents(incidents: list[dict]) -> list[dict]:
    """Merge incidents whose [start, end] intervals overlap or touch.

    Incidents with no end_seconds (unresolved) are treated as extending to
    infinity, so they merge with anything starting after them.
    """
    resolved = [i for i in incidents if i.get("start_seconds") is not None]
    resolved.sort(key=lambda i: i["start_seconds"])

    groups: list[dict] = []
    for incident in resolved:
        start = incident["start_seconds"]
        end = incident["end_seconds"] if incident["end_seconds"] is not None else float("inf")

        if groups and start <= groups[-1]["end"]:
            group = groups[-1]
            group["incidents"].append(incident)
            group["end"] = max(group["end"], end)
            group["overlap_start"] = max(group["overlap_start"], start)
        else:
            groups.append({
                "incidents": [incident],
                "end": end,
                "overlap_start": start,
            })
    return groups


def pick_frame_timestamp(group: dict, offset_seconds: float) -> float:
    """Pick a timestamp inside the overlap, nudged past the start to avoid
    the transition moment where the violation just began (often blurry/
    mid-motion on real footage)."""
    earliest_end = min(
        (i["end_seconds"] for i in group["incidents"] if i["end_seconds"] is not None),
        default=group["overlap_start"] + offset_seconds + 1,
    )
    candidate = group["overlap_start"] + offset_seconds
    return min(candidate, earliest_end - 0.1) if earliest_end > group["overlap_start"] else group["overlap_start"]


def extract_frame(video_path, timestamp_seconds, output_path):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_seconds * 1000)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"Could not read frame at {timestamp_seconds}s")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), frame)
    return output_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--incident-json", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--offset-seconds", type=float, default=2.0,
        help="How far past the overlap start to sample the frame, to avoid a transition/blur moment.",
    )
    args = parser.parse_args()

    incident_path = Path(args.incident_json)
    with open(incident_path, encoding="utf-8") as f:
        doc = json.load(f)

    groups = merge_overlapping_incidents(doc.get("incidents", []))
    output_dir = Path(args.output_dir)

    for idx, group in enumerate(groups, start=1):
        ts = pick_frame_timestamp(group, args.offset_seconds)
        frame_filename = f"evidence_{idx:02d}_{ts:.1f}s.jpg"
        frame_path = output_dir / frame_filename
        extract_frame(args.video, ts, frame_path)
        relative_path = f"evidence/{frame_filename}"
        violated = [item for inc in group["incidents"] for item in inc["violated_items"]]
        for incident in group["incidents"]:
            incident["evidence"] = [{
                "frame_path": relative_path,
                "timestamp_seconds": ts,
                "violated_items_in_frame": violated,
            }]
        ids = [i["incident_id"] for i in group["incidents"]]
        print(f"Group {idx}: overlap starts {group['overlap_start']}s -> sampled {ts}s -> {frame_path} (covers {len(group['incidents'])} incident(s): {ids})")

    with open(incident_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    print(f"Updated {incident_path}")


if __name__ == "__main__":
    main()
