"""Telegram notification engine for AREA-42 Watch Out live stream pipeline.

Triggered after each segment is processed and merged into the incident timeline.
Sends a Telegram message (with photo evidence if available) for each new
PPE violation incident, with per-incident cooldown to prevent duplicate alerts.
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

_PPE_DISPLAY = {
    "hard_hat": "Hard Hat",
    "safety_vest": "Safety Vest",
    "safety_glasses": "Safety Glasses",
    "gloves": "Gloves",
}


def _fmt_seconds(s: float | None) -> str:
    if s is None:
        return "?"
    minutes = int(s) // 60
    seconds = int(s) % 60
    return f"{minutes:02d}:{seconds:02d}"


class TelegramNotifier:
    """Sends Telegram alerts for PPE violations.

    Thread-safe: notify_if_needed is called from SegmentDispatcher worker threads.
    """

    def __init__(
        self,
        token: str,
        chat_id: str,
        cooldown_seconds: float = 60.0,
    ) -> None:
        self._token = token
        self._chat_id = chat_id
        self._cooldown = cooldown_seconds
        self._notified: dict[str, float] = {}  # incident_id → last sent timestamp
        self._lock = threading.Lock()

    def notify_if_needed(self, document: dict[str, Any]) -> None:
        """Check merged timeline document for new violations and send alerts."""
        if not document.get("incident_detected"):
            return

        for incident in document.get("incidents", []):
            incident_id = incident.get("incident_id", "")
            now = time.time()

            with self._lock:
                last_sent = self._notified.get(incident_id, 0.0)
                if now - last_sent < self._cooldown:
                    continue
                self._notified[incident_id] = now

            try:
                self._send(incident)
            except Exception as exc:
                logger.error(
                    "[TELEGRAM] Failed to send notification for %s: %s",
                    incident_id,
                    exc,
                )

    def _send(self, incident: dict[str, Any]) -> None:
        violated = incident.get("violated_items", [])
        items_str = ", ".join(_PPE_DISPLAY.get(i, i) for i in violated)
        person = incident.get("person_id") or "worker"
        start = _fmt_seconds(incident.get("start_seconds"))
        end = _fmt_seconds(incident.get("end_seconds"))
        status = incident.get("status", "")
        resolved_tag = " (resolved)" if status == "resolved" else " (ongoing)"

        caption = (
            f"⚠️ PPE VIOLATION DETECTED\n"
            f"Worker: {person}\n"
            f"Missing: {items_str}{resolved_tag}\n"
            f"Time: {start} – {end}"
        )

        evidence = incident.get("evidence", [])
        photo_path: Path | None = None
        for ev in evidence:
            p = Path(ev.get("path", ""))
            if p.exists():
                photo_path = p
                break

        base_url = f"https://api.telegram.org/bot{self._token}"

        if photo_path:
            with photo_path.open("rb") as fh:
                resp = requests.post(
                    f"{base_url}/sendPhoto",
                    data={"chat_id": self._chat_id, "caption": caption},
                    files={"photo": (photo_path.name, fh, "image/jpeg")},
                    timeout=15,
                )
        else:
            resp = requests.post(
                f"{base_url}/sendMessage",
                json={"chat_id": self._chat_id, "text": caption},
                timeout=15,
            )

        if not resp.ok:
            logger.error(
                "[TELEGRAM] API error %d: %s", resp.status_code, resp.text[:200]
            )
        else:
            logger.info(
                "[TELEGRAM] Alert sent for incident %s (%s)",
                incident.get("incident_id"),
                items_str,
            )
