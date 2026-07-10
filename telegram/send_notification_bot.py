#!/usr/bin/env python3
"""Telegram Safety Notification Bot for AREA-42 "Watch Out".

Parses normalized incident JSON or frame pipeline incident JSON and sends
alerts containing safety violation details (and evidence frame images, if available)
to a Telegram channel/chat.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv

# Ensure we load the environment variables from the project root
REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=REPO_ROOT / ".env")

# Reconfigure stdout/stderr to use UTF-8 encoding (resolves Windows terminal print errors with emojis)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send Telegram alerts with safety violations and evidence images."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the incident/pipeline JSON file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print notifications to stdout; do not send to Telegram.",
    )
    return parser.parse_args()


def format_telegram_message(
    video_id: str,
    incident: dict,
    global_summary: str | None = None
) -> str:
    # Handle different field names in different pipeline schemas
    incident_id = incident.get("incident_id", "Unknown ID")
    status = incident.get("status", "unknown")
    
    # Start and end seconds
    start_seconds = incident.get("start_seconds")
    if start_seconds is None:
        start_seconds = incident.get("start_time_seconds")
        
    end_seconds = incident.get("end_seconds")
    if end_seconds is None:
        end_seconds = incident.get("end_time_seconds")
        
    duration = incident.get("duration_seconds")
    
    # Violations / PPE Items
    violated_items = incident.get("violated_items", [])
    if not violated_items:
        ppe_type = incident.get("type", "ppe_violation")
        violated_items = [ppe_type]
        
    items_str = ", ".join(violated_items).replace("_", " ").title()
    
    # Explanations / messages
    message = incident.get("message")
    if not message and global_summary:
        message = global_summary
    if not message:
        message = f"Worker detected without proper {items_str}."
        
    # Format time ranges nicely
    start_str = f"{start_seconds:.1f}s" if isinstance(start_seconds, (int, float)) else "Start"
    end_str = f"{end_seconds:.1f}s" if isinstance(end_seconds, (int, float)) else "Ongoing"
    
    duration_str = f"{duration:.1f}s" if isinstance(duration, (int, float)) else "N/A"
    
    status_emoji = "⚠️" if "unresolved" in status or "open" in status else "✅"
    status_label = status.replace("_", " ").title()

    msg = (
        f"🚨 <b>Watch Out - Safety Violation</b> 🚨\n\n"
        f"📹 <b>Video:</b> <code>{video_id}</code>\n"
        f"🆔 <b>Incident ID:</b> <code>{incident_id}</code>\n"
        f"📦 <b>Violation:</b> {items_str}\n"
        f"🕒 <b>Timeline:</b> {start_str} - {end_str}\n"
        f"⏱️  <b>Duration:</b> {duration_str}\n"
        f"{status_emoji} <b>Status:</b> <b>{status_label}</b>\n\n"
        f"📝 <b>Details:</b> {message}\n"
    )
    return msg


def send_telegram_alert(
    token: str,
    chat_id: str,
    message: str,
    photo_path: Path | None = None
) -> bool:
    try:
        # Check if there is an image to send
        if photo_path and photo_path.exists():
            print(f"Sending Telegram photo: {photo_path}...")
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            with open(photo_path, "rb") as photo_file:
                files = {"photo": photo_file}
                data = {
                    "chat_id": chat_id,
                    "caption": message,
                    "parse_mode": "HTML",
                }
                response = requests.post(url, data=data, files=files, timeout=30)
        else:
            print("Sending Telegram text message (no photo)...")
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
            }
            response = requests.post(url, json=payload, timeout=30)
            
        if response.status_code == 200:
            print("Telegram alert sent successfully.")
            return True
        else:
            print(
                f"Failed to send Telegram alert. Status: {response.status_code}, "
                f"Response: {response.text}",
                file=sys.stderr,
            )
            return False
            
    except Exception as e:
        print(f"Error communicating with Telegram API: {e}", file=sys.stderr)
        return False


def main() -> None:
    args = parse_arguments()
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"Error: Input JSON file not found at '{input_path}'", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error: Failed to parse input JSON. {e}", file=sys.stderr)
        sys.exit(1)
        
    # Extract video ID/name
    video_path_str = data.get("video", "")
    if not video_path_str:
        video_path_str = data.get("video_id", "")
    video_id = Path(video_path_str).name or "unknown_video"
    
    incidents = data.get("incidents", [])
    global_summary = data.get("summary")
    
    if not incidents:
        print("No incidents found in the JSON file. No notification needed.")
        sys.exit(0)
        
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    is_dry_run = args.dry_run or not token or not chat_id
    
    if not token or not chat_id:
        print(
            "WARNING: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found in .env.\n"
            "Running in simulation/dry-run mode.",
            file=sys.stderr,
        )
        
    for incident in incidents:
        # Determine the first available evidence frame image path
        photo_path = None
        # Try native video frame pipeline schema
        start_frame = incident.get("start_evidence_frame")
        last_seen_frame = incident.get("last_seen_violation_frame")
        
        frame_candidate = start_frame or last_seen_frame
        if frame_candidate:
            photo_candidate = REPO_ROOT / frame_candidate
            if photo_candidate.exists():
                photo_path = photo_candidate
            else:
                # If absolute path was specified
                path_abs = Path(frame_candidate)
                if path_abs.exists():
                    photo_path = path_abs
                    
        # Try incident contract evidence list schema
        evidence_list = incident.get("evidence", [])
        if not photo_path and isinstance(evidence_list, list):
            for ev in evidence_list:
                ev_path = ev.get("frame_path")
                if ev_path:
                    ev_candidate = REPO_ROOT / ev_path
                    if ev_candidate.exists():
                        photo_path = ev_candidate
                        break
                    path_abs = Path(ev_path)
                    if path_abs.exists():
                        photo_path = path_abs
                        break
                        
        message = format_telegram_message(video_id, incident, global_summary)
        
        if is_dry_run:
            print("\n--- [SIMULATION] TELEGRAM NOTIFICATION ---")
            print(f"To Chat ID: {chat_id or '<unconfigured>'}")
            if photo_path:
                print(f"With Evidence Image: {photo_path}")
            print("Message Content:")
            print(message)
            print("------------------------------------------\n")
        else:
            send_telegram_alert(token, chat_id, message, photo_path)


if __name__ == "__main__":
    main()
