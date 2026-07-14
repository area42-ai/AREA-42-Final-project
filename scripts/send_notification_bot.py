#!/usr/bin/env python3
"""Send grouped, stateful Watch Out notifications or serve callback buttons."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from telegram_notifier import TelegramNotifier


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch Out Telegram notification service")
    parser.add_argument("--input", help="Incident JSON file")
    parser.add_argument("--camera-name", default=os.getenv("CAMERA_NAME", "Camera-1"))
    parser.add_argument(
        "--state-file",
        default=os.getenv(
            "TELEGRAM_STATE_FILE", str(REPO_ROOT / "data/telegram_notification_state.json")
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--listen-callbacks",
        action="store_true",
        help="Continuously process mute buttons (can be run as a separate service).",
    )
    args = parser.parse_args()
    if not args.input and not args.listen_callbacks:
        parser.error("Either --input or --listen-callbacks is required")
    return args


def _notifier(args: argparse.Namespace) -> TelegramNotifier:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be defined in .env")
    return TelegramNotifier(
        token=token,
        chat_id=chat_id,
        camera_name=args.camera_name,
        state_path=args.state_file,
        recurring_seconds=float(os.getenv("TELEGRAM_RECURRING_SECONDS", "300")),
    )


def main() -> None:
    args = parse_arguments()
    if args.dry_run:
        if not args.input:
            print("Dry-run callback listener cannot be started.")
            return
        document = json.loads(Path(args.input).read_text(encoding="utf-8"))
        # Isolated dummy state; no network operation is performed.
        captured: list[tuple[str, dict, Path | None]] = []
        with tempfile.TemporaryDirectory() as temp_dir:
            notifier = TelegramNotifier(
                "dry-run", "dry-run", args.camera_name, Path(temp_dir) / "state.json"
            )
            notifier._send = lambda message, keyboard, photo: captured.append((message, keyboard, photo)) or True  # type: ignore[method-assign]
            notifier.notify_if_needed(document)
        if captured:
            print(captured[0][0])
            print(json.dumps(captured[0][1], ensure_ascii=False, indent=2))
        else:
            print("No new state changes to send.")
        return

    try:
        notifier = _notifier(args)
    except RuntimeError as exc:
        print(f"Telegram notifications disabled: {exc}", file=sys.stderr)
        return
    if args.input:
        document = json.loads(Path(args.input).read_text(encoding="utf-8"))
        notifier.notify_if_needed(document)
    if args.listen_callbacks:
        print(f"Polling CallbackQuery (camera: {args.camera_name}). Press Ctrl+C to stop.")
        try:
            while True:
                notifier.poll_callbacks_once()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
