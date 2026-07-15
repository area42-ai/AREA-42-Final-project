"""Camera streaming Blueprint for Flask.

Provides two endpoints:
  GET /api/cameras        — enumerate available cameras on this machine
  GET /api/stream/<int:id> — MJPEG multipart stream for a given camera index

Each camera stream runs its own OpenCV capture in a background thread so
multiple cameras can be served simultaneously without blocking.

Raw numpy frames are also stored alongside JPEG bytes so the in-process
AI pipeline thread can read them without opening the camera a second time.
"""

from __future__ import annotations

import subprocess
import threading
import time
from typing import Generator

import cv2
import numpy as np
from flask import Blueprint, Response, jsonify

camera_bp = Blueprint("camera_stream", __name__)

# ---------------------------------------------------------------------------
# Camera registry — shared state for active captures
# ---------------------------------------------------------------------------
_camera_locks: dict[int, threading.Lock] = {}
_camera_captures: dict[int, cv2.VideoCapture] = {}
_camera_frames: dict[int, bytes | None] = {}          # JPEG bytes for MJPEG
_camera_raw_frames: dict[int, np.ndarray | None] = {} # raw numpy for pipeline
_camera_threads: dict[int, threading.Thread] = {}

MAX_CAMERA_PROBE = 5  # try indices 0..4 during enumeration


def _get_camera_names_from_wmi() -> list[str]:
    """Query Windows WMI for camera device names in enumeration order."""
    cmd = [
        "powershell", "-NoProfile", "-Command",
        (
            "Get-CimInstance Win32_PnPEntity "
            "| Where-Object { $_.PNPClass -eq 'Camera' -or $_.PNPClass -eq 'Image' } "
            "| Select-Object -ExpandProperty Name"
        ),
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
        if res.returncode == 0 and res.stdout.strip():
            return [l.strip() for l in res.stdout.strip().splitlines() if l.strip()]
    except Exception:
        pass
    return []


def _classify_camera_name(wmi_name: str, fallback_index: int) -> str:
    """Return a user-friendly label derived from the WMI device name."""
    lower = wmi_name.lower()
    builtin_keywords = ("integrated", "built-in", "built in", "ir camera", "front", "internal")
    if any(kw in lower for kw in builtin_keywords):
        return f"Built-in Webcam ({wmi_name})"
    return f"External Camera ({wmi_name})"


def _get_physical_camera_count() -> int:
    """Query Windows WMI to get the number of physical camera devices."""
    names = _get_camera_names_from_wmi()
    if names:
        return len(names)
    # Legacy fallback
    cmd = [
        "powershell", "-NoProfile", "-Command",
        (
            "Get-CimInstance Win32_PnPEntity "
            "| Where-Object { $_.PNPClass -eq 'Camera' -or $_.PNPClass -eq 'Image' } "
            "| Select-Object Name | ConvertTo-Json"
        ),
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        if res.returncode == 0 and res.stdout.strip():
            import json
            data = json.loads(res.stdout)
            if isinstance(data, dict):
                return 1
            elif isinstance(data, list):
                return len(data)
    except Exception:
        pass
    return 1


def _enumerate_cameras() -> list[dict]:
    """Probe camera indices and return only physical camera devices."""
    wmi_names = _get_camera_names_from_wmi()
    physical_count = len(wmi_names) if wmi_names else _get_physical_camera_count()

    cameras: list[dict] = []
    found_count = 0
    for idx in range(MAX_CAMERA_PROBE):
        if found_count >= physical_count:
            break

        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()

            # Use WMI name if available, else generic fallback
            if found_count < len(wmi_names):
                friendly_name = _classify_camera_name(wmi_names[found_count], found_count)
            else:
                friendly_name = f"Camera {found_count + 1}"

            cameras.append({
                "id": idx,
                "name": friendly_name,
                "resolution": f"{w}x{h}",
            })
            found_count += 1

    # Fallback if no cameras could be opened but we expected some
    if not cameras:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if cap.isOpened():
            cap.release()
            cameras.append({
                "id": 0,
                "name": "Camera 1",
                "resolution": "640x480",
            })

    return cameras


def _capture_loop(camera_id: int) -> None:
    """Background thread: continuously grab frames from *camera_id*."""
    cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    _camera_captures[camera_id] = cap

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.05)
            continue
        _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        with _camera_locks[camera_id]:
            _camera_frames[camera_id] = jpeg.tobytes()
            _camera_raw_frames[camera_id] = frame  # kept for pipeline thread
        time.sleep(0.03)  # ~30 fps cap

    cap.release()


def get_raw_frame(camera_id: int) -> np.ndarray | None:
    """Return the most recent raw numpy frame for *camera_id*.

    Called by the in-process pipeline thread; never opens the camera itself.
    Returns None when no frame is available yet (pipeline should skip/wait).
    """
    lock = _camera_locks.get(camera_id)
    if lock is None:
        return None
    with lock:
        frame = _camera_raw_frames.get(camera_id)
        return frame.copy() if frame is not None else None


def release_camera(camera_id: int) -> None:
    """Release a camera capture so an external process can open it.

    Kept for backwards-compatibility. Not called during normal in-process
    pipeline operation — the pipeline thread reads from get_raw_frame() instead.
    """
    cap = _camera_captures.pop(camera_id, None)
    if cap is not None:
        cap.release()


def _ensure_capture_thread(camera_id: int) -> None:
    """Start a background capture thread for *camera_id* if not already running."""
    if camera_id in _camera_threads and _camera_threads[camera_id].is_alive():
        return
    _camera_locks[camera_id] = threading.Lock()
    _camera_frames[camera_id] = None
    _camera_raw_frames[camera_id] = None
    t = threading.Thread(target=_capture_loop, args=(camera_id,), daemon=True)
    _camera_threads[camera_id] = t
    t.start()


def _mjpeg_generator(camera_id: int) -> Generator[bytes, None, None]:
    """Yield MJPEG multipart frames for the given camera."""
    while True:
        frame_bytes: bytes | None = None
        lock = _camera_locks.get(camera_id)
        if lock:
            with lock:
                frame_bytes = _camera_frames.get(camera_id)
        if frame_bytes is None:
            time.sleep(0.05)
            continue
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )
        time.sleep(0.033)  # ~30 fps


# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------
@camera_bp.route("/api/cameras", methods=["GET"])
def list_cameras():
    """Return JSON list of available camera devices."""
    cameras = _enumerate_cameras()
    return jsonify({"cameras": cameras})


@camera_bp.route("/api/stream/<int:camera_id>")
def stream_camera(camera_id: int):
    """Return an MJPEG stream for the requested camera index."""
    _ensure_capture_thread(camera_id)
    return Response(
        _mjpeg_generator(camera_id),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )
