"""Stateful, grouped Telegram notifications for Watch Out PPE incidents."""

from __future__ import annotations

import html
import copy
import json
import logging
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import requests

logger = logging.getLogger(__name__)

_PPE_DISPLAY = {
    "hard_hat": "Hard hat",
    "safety_vest": "Safety vest",
    "safety_glasses": "Safety glasses",
    "gloves": "Gloves",
}
_OPEN_STATUSES = {"open", "unresolved", "unresolved_after_last_confirmed_violation"}


def _now_text(now: datetime | None = None) -> str:
    return (now or datetime.now().astimezone()).strftime("%d.%m.%Y - %H:%M:%S")


def _incident_items(incident: dict[str, Any]) -> list[str]:
    items = incident.get("violated_items") or []
    if not items and incident.get("ppe_item"):
        items = [incident["ppe_item"]]
    if not items and incident.get("type"):
        items = [incident["type"]]
    return [str(item) for item in items]


def _is_open(incident: dict[str, Any]) -> bool:
    status = str(incident.get("status", "")).lower()
    return status in _OPEN_STATUSES or (
        not status and incident.get("end_seconds") is None
    )


def _evidence_path(incidents: list[dict[str, Any]]) -> Path | None:
    for incident in incidents:
        candidates = [
            incident.get("start_evidence_frame"),
            incident.get("last_seen_violation_frame"),
        ]
        candidates.extend(
            ev.get("path") or ev.get("frame_path")
            for ev in incident.get("evidence", [])
            if isinstance(ev, dict)
        )
        for candidate in candidates:
            if candidate:
                path = Path(candidate)
                if path.exists() and path.is_file():
                    return path
    return None


class TelegramNotifier:
    """Tracks incident transitions and sends one grouped message per update.

    State is persisted so restarts do not turn recurring incidents into first
    alerts or forget muted Validation IDs / violation types.
    """

    def __init__(
        self,
        token: str,
        chat_id: str,
        camera_name: str = "Kamera-1",
        state_path: str | Path = "data/telegram_notification_state.json",
        recurring_seconds: float = 300.0,
        request_timeout: float = 30.0,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._token = token
        self._chat_id = str(chat_id)
        self.camera_name = camera_name
        self._state_path = Path(state_path)
        self._recurring_seconds = recurring_seconds
        self._timeout = request_timeout
        self._clock = clock
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._listener: threading.Thread | None = None
        self._state = self._load_state()

    def _empty_state(self) -> dict[str, Any]:
        return {
            "version": 1,
            "incidents": {},
            "last_resolved_by_rule": {},
            "muted_validation_ids": [],
            "muted_violation_types": [],
            "update_offset": 0,
        }

    def _load_state(self) -> dict[str, Any]:
        try:
            loaded = json.loads(self._state_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                base = self._empty_state()
                base.update(loaded)
                return base
        except FileNotFoundError:
            pass
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("[TELEGRAM] Could not read state file: %s", exc)
        return self._empty_state()

    def _save_state(self) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._state_path.with_suffix(self._state_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(self._state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(self._state_path)

    def notify_if_needed(self, document: dict[str, Any]) -> bool:
        """Send at most one grouped message for all transitions in document."""
        incidents = [i for i in document.get("incidents", []) if isinstance(i, dict)]
        document_id = str(document.get("video_id") or document.get("video") or "stream")
        now = self._clock()
        changes: list[dict[str, Any]] = []

        with self._lock:
            state_before = copy.deepcopy(self._state)
            for position, incident in enumerate(incidents, start=1):
                person = str(incident.get("person_id") or "worker")
                for item in _incident_items(incident):
                    start_marker = incident.get(
                        "start_seconds", incident.get("start_time_seconds", position)
                    )
                    # Timeline managers may renumber incident_001/002 when an
                    # earlier segment finishes late. Person + rule + immutable
                    # event start remains a stable identity across rebuilds.
                    state_key = (
                        f"{self.camera_name}|{document_id}|{person}|{item}|{start_marker}"
                    )
                    rule_key = f"{self.camera_name}|{person}|{item}"
                    current_open = _is_open(incident)
                    tracked = self._state["incidents"].get(state_key)

                    if tracked is None:
                        validation_id = str(uuid.uuid4())
                        last_resolved = self._state["last_resolved_by_rule"].get(rule_key)
                        if isinstance(last_resolved, dict):
                            resolved_at = last_resolved.get("timestamp")
                            prior_validation_id = last_resolved.get("validation_id")
                        else:  # Backward-compatible with version-1 numeric state.
                            resolved_at = last_resolved
                            prior_validation_id = None
                        recurring = bool(
                            current_open
                            and resolved_at is not None
                            and now - float(resolved_at) <= self._recurring_seconds
                        )
                        if recurring and prior_validation_id:
                            validation_id = str(prior_validation_id)
                        tracked = {
                            "validation_id": validation_id,
                            "rule_key": rule_key,
                            "item": item,
                            "open": current_open,
                            "last_seen": now,
                        }
                        self._state["incidents"][state_key] = tracked
                        changes.append({
                            "kind": ("recurring" if recurring else "first")
                            if current_open
                            else "resolved",
                            "validation_id": validation_id,
                            "item": item,
                            "incident": incident,
                        })
                        if not current_open:
                            self._state["last_resolved_by_rule"][rule_key] = {
                                "timestamp": now,
                                "validation_id": validation_id,
                            }
                        continue

                    was_open = bool(tracked.get("open"))
                    tracked["last_seen"] = now
                    if was_open and not current_open:
                        tracked["open"] = False
                        self._state["last_resolved_by_rule"][rule_key] = {
                            "timestamp": now,
                            "validation_id": tracked["validation_id"],
                        }
                        changes.append({
                            "kind": "resolved",
                            "validation_id": tracked["validation_id"],
                            "item": item,
                            "incident": incident,
                        })
                    elif not was_open and current_open:
                        # Reopening inside the same lifecycle keeps its
                        # Validation_ID, making yellow -> green -> orange
                        # traceable with one reference.
                        validation_id = tracked["validation_id"]
                        tracked["open"] = True
                        changes.append({
                            "kind": "recurring",
                            "validation_id": validation_id,
                            "item": item,
                            "incident": incident,
                        })

            filtered = [change for change in changes if not self._is_muted(change)]
            self._save_state()
            if not filtered:
                return False

            message = self.format_grouped_message(filtered)
            keyboard = self._build_keyboard(filtered)
            photo_path = _evidence_path([change["incident"] for change in filtered])
            sent = self._send(message, keyboard, photo_path)
            if not sent:
                # A transient Telegram failure must not consume the transition;
                # the next document update should retry the same notification.
                self._state = state_before
                self._save_state()
            return sent

    def _is_muted(self, change: dict[str, Any]) -> bool:
        return (
            change["validation_id"] in self._state["muted_validation_ids"]
            or change["item"] in self._state["muted_violation_types"]
        )

    def format_grouped_message(
        self, changes: list[dict[str, Any]], now: datetime | None = None
    ) -> str:
        icons = {"first": "🟡", "resolved": "🟢", "recurring": "🟠"}
        labels = {
            "first": "FIRST WARNING",
            "resolved": "VIOLATION RESOLVED",
            "recurring": "RECURRING VIOLATION",
        }
        lines = [
            "<b>WATCH OUT — PPE STATE NOTIFICATION</b>",
            f"📷 <b>Camera:</b> {html.escape(self.camera_name)}",
            f"🕒 <b>Date and Time:</b> {_now_text(now)}",
            "",
        ]
        for change in changes:
            kind = change["kind"]
            item = _PPE_DISPLAY.get(change["item"], change["item"].replace("_", " ").title())
            lines.extend([
                f"{icons[kind]} <b>{labels[kind]}</b>",
                f"• Violation: {html.escape(item)}",
                f"• Validation_ID: <code>{html.escape(change['validation_id'])}</code>",
                "",
            ])
        return "\n".join(lines).rstrip()

    def _build_keyboard(self, changes: list[dict[str, Any]]) -> dict[str, Any]:
        rows = []
        seen: set[str] = set()
        for change in changes:
            validation_id = change["validation_id"]
            if validation_id in seen:
                continue
            seen.add(validation_id)
            short = validation_id.split("-")[0]
            rows.append([{
                "text": f"🔕 Mute ({short})",
                "callback_data": f"mute_id:{validation_id}",
            }])
        return {"inline_keyboard": rows}

    def _send(
        self,
        message: str,
        keyboard: dict[str, Any],
        photo_path: Path | None,
    ) -> bool:
        base_url = f"https://api.telegram.org/bot{self._token}"
        if photo_path:
            with photo_path.open("rb") as photo:
                response = requests.post(
                    f"{base_url}/sendPhoto",
                    data={
                        "chat_id": self._chat_id,
                        "caption": message,
                        "parse_mode": "HTML",
                        "reply_markup": json.dumps(keyboard, ensure_ascii=False),
                    },
                    files={"photo": (photo_path.name, photo, "image/jpeg")},
                    timeout=self._timeout,
                )
        else:
            response = requests.post(
                f"{base_url}/sendMessage",
                json={
                    "chat_id": self._chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "reply_markup": keyboard,
                },
                timeout=self._timeout,
            )
        if not response.ok:
            logger.error("[TELEGRAM] API error %d: %s", response.status_code, response.text[:300])
            return False
        logger.info("[TELEGRAM] %d state changes sent in a single message.", len(keyboard["inline_keyboard"]))
        return True

    def process_callback_query(self, query: dict[str, Any]) -> bool:
        """Apply a ``mute_id:<UUID>`` CallbackQuery and acknowledge it."""
        query_id = str(query.get("id", ""))
        data = str(query.get("data", ""))
        message_chat = str(query.get("message", {}).get("chat", {}).get("id", ""))
        accepted = message_chat == self._chat_id and data.startswith("mute_id:")
        answer = "This notification has been muted." if accepted else "This action is invalid."
        if accepted:
            validation_id = data.removeprefix("mute_id:")
            with self._lock:
                if validation_id not in self._state["muted_validation_ids"]:
                    self._state["muted_validation_ids"].append(validation_id)
                self._save_state()
        if query_id:
            requests.post(
                f"https://api.telegram.org/bot{self._token}/answerCallbackQuery",
                json={"callback_query_id": query_id, "text": answer},
                timeout=self._timeout,
            )
        return accepted

    def poll_callbacks_once(self, timeout_seconds: int = 25) -> int:
        with self._lock:
            offset = int(self._state.get("update_offset", 0))
        response = requests.get(
            f"https://api.telegram.org/bot{self._token}/getUpdates",
            params={
                "offset": offset,
                "timeout": timeout_seconds,
                "allowed_updates": json.dumps(["callback_query"]),
            },
            timeout=timeout_seconds + 5,
        )
        response.raise_for_status()
        updates = response.json().get("result", [])
        handled = 0
        for update in updates:
            callback = update.get("callback_query")
            if isinstance(callback, dict) and self.process_callback_query(callback):
                handled += 1
            with self._lock:
                self._state["update_offset"] = max(
                    int(self._state.get("update_offset", 0)), int(update["update_id"]) + 1
                )
                self._save_state()
        return handled

    def start_callback_listener(self) -> None:
        if self._listener and self._listener.is_alive():
            return
        self._stop_event.clear()
        self._listener = threading.Thread(
            target=self._callback_loop, name="telegram-callback-listener", daemon=True
        )
        self._listener.start()

    def _callback_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.poll_callbacks_once()
            except Exception as exc:
                logger.warning("[TELEGRAM] Callback listener error: %s", exc)
                self._stop_event.wait(3)

    def stop_callback_listener(self) -> None:
        self._stop_event.set()
        if self._listener:
            self._listener.join(timeout=2)
