"""Camera streaming Blueprint for Flask.

Provides two endpoints:
  GET /api/cameras        — enumerate available cameras on this machine
  GET /api/stream/<int:id> — MJPEG multipart stream for a given camera index

Each camera stream runs its own OpenCV capture in a background thread so
multiple cameras can be served simultaneously without blocking.
"""

from __future__ import annotations

import threading
import time
from typing import Generator

import cv2
from flask import Blueprint, Response, jsonify

camera_bp = Blueprint("camera_stream", __name__)

# ---------------------------------------------------------------------------
# Camera registry — shared state for active captures
# ---------------------------------------------------------------------------
_camera_locks: dict[int, threading.Lock] = {}
_camera_captures: dict[int, cv2.VideoCapture] = {}
_camera_frames: dict[int, bytes | None] = {}
_camera_threads: dict[int, threading.Thread] = {}


MAX_CAMERA_PROBE = 5  # try indices 0..4 during enumeration


def _get_physical_camera_count() -> int:
    """Query Windows WMI to get the number of physical camera devices."""
    import subprocess
    import json
    cmd = ["powershell", "-NoProfile", "-Command", 
           "Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPClass -eq 'Camera' -or $_.PNPClass -eq 'Image' } | Select-Object Name | ConvertTo-Json"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            if isinstance(data, dict):
                return 1
            elif isinstance(data, list):
                return len(data)
    except Exception:
        pass
    return 1  # default fallback


def _enumerate_cameras() -> list[dict]:
    """Probe camera indices and return only physical camera devices."""
    cameras: list[dict] = []
    physical_count = _get_physical_camera_count()
    
    found_count = 0
    for idx in range(MAX_CAMERA_PROBE):
        if found_count >= physical_count:
            break
            
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cameras.append({
                "id": idx,
                "name": f"Camera {found_count + 1}",
                "resolution": f"{w}x{h}",
            })
            cap.release()
            found_count += 1
            
    # Fallback if no cameras could be opened but we expected some
    if not cameras:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if cap.isOpened():
            cameras.append({
                "id": 0,
                "name": "Camera 1",
                "resolution": "640x480",
            })
            cap.release()
            
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
        _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        with _camera_locks[camera_id]:
            _camera_frames[camera_id] = jpeg.tobytes()
        time.sleep(0.03)  # ~30 fps cap

    cap.release()


def release_camera(camera_id: int) -> None:
    """Release a camera capture so an external process can open it.

    The background capture thread exits naturally once cap.isOpened() returns
    False. The next /api/stream/<id> request will re-open the camera via
    _ensure_capture_thread.
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
    t = threading.Thread(target=_capture_loop, args=(camera_id,), daemon=True)
    _camera_threads[camera_id] = t
    t.start()


def _mjpeg_generator(camera_id: int) -> Generator[bytes, None, None]:
    """Yield MJPEG multipart frames for the given camera."""
    while True:
        frame_bytes: bytes | None = None
        with _camera_locks.get(camera_id, threading.Lock()):
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
