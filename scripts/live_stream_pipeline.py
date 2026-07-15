"""AREA-42 Watch Out: event-driven live stream pipeline.

Replaces fixed 10-second chunking with an event-driven architecture:

    RTSP frames
        -> Lightweight Perception Layer   (cheap motion/person gate)
        -> Active Buffer Manager          (event-driven variable-length segments,
                                            rotated on duration/size caps)
        -> Segment Dispatcher             (bounded worker pool -> Pipeline A,
                                            i.e. Nemotron -> Gemma, unchanged)
        -> Incident State Manager         (cross-segment incident continuity)
        -> Evidence Manager               (keyframe evidence attached to
                                            incidents in the merged timeline)

Nemotron, Gemma, the Incident Contract, and Pipeline A itself are unchanged;
this file only changes WHEN and WHAT is dispatched to them.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

import cv2
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=REPO_ROOT / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from active_buffer_manager import ActiveBufferManager
from evidence_manager import EvidenceManager
from incident_state_manager import IncidentStateManager
from perception_layer import PerceptionLayer
from segment_dispatcher import SegmentDispatcher
from telegram_notifier import TelegramNotifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# CAMERA_SOURCE: "0" (or any integer) = local webcam index; RTSP URL = IP camera
_cam_env = os.getenv("CAMERA_SOURCE", "0")
CAMERA_SOURCE: int | str = int(_cam_env) if _cam_env.isdigit() else _cam_env
TARGET_FPS = 4                       # Nemotron's optimal processing speed
RESOLUTION = (1280, 720)             # Downscaled to prevent 500 API errors

PRE_ROLL_SECONDS = 2.0               # captured before an event is detected
POST_ROLL_SECONDS = 3.0              # captured after activity ends (debounce)
MIN_SEGMENT_SECONDS = 1.5            # shorter events are discarded as noise

# Long-running events are rotated into consecutive segments rather than
# growing without bound, since oversized clips cause hosted Nemotron
# inference to time out. IncidentStateManager stitches the resulting
# consecutive segments back into one logical incident.
MAX_EVENT_DURATION_SECONDS = 18.0    # configurable, recommended range 15-20s
MAX_SEGMENT_SIZE_BYTES = 7 * 1024 * 1024  # configurable, ~7MB

DISPATCH_MAX_WORKERS = 3
GEMMA_MODEL = None                   # None => gemma_text_to_incident.py default
PPE_ITEMS = None                     # None => full default PPE scope


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AREA-42 Watch Out: event-driven live stream pipeline."
    )
    parser.add_argument(
        "--camera",
        default=None,
        help=(
            "Camera source: integer index (0, 1, ...) or RTSP URL. "
            "Overrides CAMERA_SOURCE in .env. Default: 0."
        ),
    )
    parser.add_argument(
        "--video-id",
        default="live_stream",
        help=(
            "Logical name for this stream. Used to namespace output directories "
            "so multiple instances don't collide. Default: live_stream."
        ),
    )
    parser.add_argument(
        "--camera-name",
        default=os.getenv("CAMERA_NAME", "Kamera-1"),
        help="Bildirimlerde gösterilecek benzersiz kamera adı/numarası.",
    )
    return parser.parse_args()


def start_stream(args: argparse.Namespace) -> None:
    # Camera source: CLI arg > env var > default 0
    if args.camera is not None:
        cam_raw = args.camera
    else:
        cam_raw = os.getenv("CAMERA_SOURCE", "0")
    camera_source: int | str = int(cam_raw) if str(cam_raw).isdigit() else cam_raw

    video_id: str = args.video_id

    # Each video_id gets its own output namespace so two instances never collide.
    # Paths are anchored to REPO_ROOT so they resolve correctly regardless of
    # the process CWD (e.g. when launched as a subprocess by the API server).
    event_segments_dir = REPO_ROOT / "data" / "event_segments" / video_id
    failed_segments_dir = REPO_ROOT / "data" / "failed_segments" / video_id
    output_logs_dir = REPO_ROOT / "data" / "output_logs" / video_id
    evidence_dir = REPO_ROOT / "data" / "evidence" / video_id
    timeline_path = REPO_ROOT / "data" / "output_logs" / video_id / "live_incident_timeline.json"

    logger.info("Connecting to camera source: %s  (video_id=%s)", camera_source, video_id)
    # Use DirectShow on Windows for local webcams — MSMF backend fails to grab frames
    # in subprocess contexts even when isOpened() returns True.
    backend = cv2.CAP_DSHOW if isinstance(camera_source, int) else cv2.CAP_ANY
    cap = cv2.VideoCapture(camera_source, backend)

    if not cap.isOpened():
        logger.error(
            "Failed to open camera source %r. "
            "Check CAMERA_SOURCE in .env or --camera flag (0 = built-in webcam).",
            camera_source,
        )
        return

    perception = PerceptionLayer()
    buffer_manager = ActiveBufferManager(
        output_dir=event_segments_dir,
        fps=TARGET_FPS,
        resolution=RESOLUTION,
        pre_roll_seconds=PRE_ROLL_SECONDS,
        post_roll_seconds=POST_ROLL_SECONDS,
        min_segment_seconds=MIN_SEGMENT_SECONDS,
        max_event_duration_seconds=MAX_EVENT_DURATION_SECONDS,
        max_segment_size_bytes=MAX_SEGMENT_SIZE_BYTES,
    )
    state_manager = IncidentStateManager(
        video_id=video_id,
        timeline_path=timeline_path,
    )
    evidence_manager = EvidenceManager(evidence_dir=evidence_dir)

    notifier: TelegramNotifier | None = None
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if tg_token and tg_chat:
        notifier = TelegramNotifier(
            token=tg_token,
            chat_id=tg_chat,
            camera_name=args.camera_name,
            state_path=REPO_ROOT / "data" / video_id / "telegram_state.json",
            recurring_seconds=float(os.getenv("TELEGRAM_RECURRING_SECONDS", "300")),
        )
        notifier.start_callback_listener()
        logger.info(
            "[TELEGRAM] Notifications enabled (chat_id=%s, camera=%s)",
            tg_chat,
            args.camera_name,
        )
    else:
        logger.warning("[TELEGRAM] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set; notifications disabled.")

    dispatcher = SegmentDispatcher(
        state_manager=state_manager,
        evidence_manager=evidence_manager,
        output_dir=output_logs_dir,
        failed_dir=failed_segments_dir,
        max_workers=DISPATCH_MAX_WORKERS,
        gemma_model=GEMMA_MODEL,
        ppe_items=PPE_ITEMS,
        notifier=notifier,
    )

    stream_start = time.time()
    frame_interval = 1.0 / TARGET_FPS
    last_capture_time = 0.0

    logger.info("Stream active. Event-driven capture running (no fixed chunk timer)...")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(1)
                continue

            now = time.time()
            if (now - last_capture_time) < frame_interval:
                continue
            last_capture_time = now

            stream_time = now - stream_start
            perception_result = perception.process_frame(frame, stream_time)
            finalized_segment = buffer_manager.add_frame(frame, perception_result)

            if finalized_segment is not None:
                logger.info(
                    "[BUFFER] Event segment closed: %s (%.1fs, %d frames)",
                    finalized_segment.path.name,
                    finalized_segment.duration_seconds,
                    finalized_segment.frame_count,
                )
                dispatcher.submit(finalized_segment)

    except KeyboardInterrupt:
        logger.info("Stopping stream capture...")
    finally:
        cap.release()
        final_segment = buffer_manager.flush(time.time() - stream_start)
        if final_segment is not None:
            dispatcher.submit(final_segment)
        dispatcher.shutdown(wait=True)
        final_document = state_manager.finalize()
        state_manager.persist(final_document)
        if notifier is not None:
            notifier.notify_if_needed(final_document)
            notifier.stop_callback_listener()
        logger.info("Pipeline shut down safely. Final timeline: %s", timeline_path)


def start_stream_from_getter(
    args: argparse.Namespace,
    frame_getter,
    stop_event: "threading.Event",
) -> None:
    """Same pipeline as start_stream() but reads frames from frame_getter() instead of
    opening a camera device.  frame_getter() must return an np.ndarray or None.
    stop_event signals a clean shutdown (set by /api/live/stop).
    """
    import threading  # local import keeps top-level imports unchanged

    video_id: str = args.video_id

    event_segments_dir = REPO_ROOT / "data" / "event_segments" / video_id
    failed_segments_dir = REPO_ROOT / "data" / "failed_segments" / video_id
    output_logs_dir = REPO_ROOT / "data" / "output_logs" / video_id
    evidence_dir = REPO_ROOT / "data" / "evidence" / video_id
    timeline_path = REPO_ROOT / "data" / "output_logs" / video_id / "live_incident_timeline.json"

    logger.info("Pipeline thread starting (frame_getter mode, video_id=%s)", video_id)

    perception = PerceptionLayer()
    buffer_manager = ActiveBufferManager(
        output_dir=event_segments_dir,
        fps=TARGET_FPS,
        resolution=RESOLUTION,
        pre_roll_seconds=PRE_ROLL_SECONDS,
        post_roll_seconds=POST_ROLL_SECONDS,
        min_segment_seconds=MIN_SEGMENT_SECONDS,
        max_event_duration_seconds=MAX_EVENT_DURATION_SECONDS,
        max_segment_size_bytes=MAX_SEGMENT_SIZE_BYTES,
    )
    state_manager = IncidentStateManager(
        video_id=video_id,
        timeline_path=timeline_path,
    )
    evidence_manager = EvidenceManager(evidence_dir=evidence_dir)

    notifier: TelegramNotifier | None = None
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if tg_token and tg_chat:
        notifier = TelegramNotifier(
            token=tg_token,
            chat_id=tg_chat,
            camera_name=getattr(args, "camera_name", "Camera-1"),
            state_path=REPO_ROOT / "data" / video_id / "telegram_state.json",
            recurring_seconds=float(os.getenv("TELEGRAM_RECURRING_SECONDS", "300")),
        )
        notifier.start_callback_listener()

    dispatcher = SegmentDispatcher(
        state_manager=state_manager,
        evidence_manager=evidence_manager,
        output_dir=output_logs_dir,
        failed_dir=failed_segments_dir,
        max_workers=DISPATCH_MAX_WORKERS,
        gemma_model=GEMMA_MODEL,
        ppe_items=PPE_ITEMS,
        notifier=notifier,
    )

    stream_start = time.time()
    frame_interval = 1.0 / TARGET_FPS
    last_capture_time = 0.0

    logger.info("Pipeline thread active (event-driven, shared frame buffer)...")

    try:
        while not stop_event.is_set():
            frame = frame_getter()
            if frame is None:
                time.sleep(0.05)
                continue

            now = time.time()
            if (now - last_capture_time) < frame_interval:
                time.sleep(0.005)
                continue
            last_capture_time = now

            stream_time = now - stream_start
            perception_result = perception.process_frame(frame, stream_time)
            finalized_segment = buffer_manager.add_frame(frame, perception_result)

            if finalized_segment is not None:
                logger.info(
                    "[BUFFER] Event segment closed: %s (%.1fs, %d frames)",
                    finalized_segment.path.name,
                    finalized_segment.duration_seconds,
                    finalized_segment.frame_count,
                )
                dispatcher.submit(finalized_segment)

    except Exception as exc:
        logger.error("Pipeline thread error: %s", exc, exc_info=True)
    finally:
        final_segment = buffer_manager.flush(time.time() - stream_start)
        if final_segment is not None:
            dispatcher.submit(final_segment)
        dispatcher.shutdown(wait=True)
        final_document = state_manager.finalize()
        state_manager.persist(final_document)
        if notifier is not None:
            notifier.notify_if_needed(final_document)
            notifier.stop_callback_listener()
        logger.info("Pipeline thread shut down. Timeline: %s", timeline_path)


if __name__ == "__main__":
    start_stream(_parse_args())
