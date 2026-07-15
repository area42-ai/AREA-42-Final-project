# Architecture — Watch Out

Current as of July 2026. Describes the implemented system, not a proposal.

---

## Overview

Watch Out has two entry points that share the same core inference pipeline (Pipeline A):

| Entry point | Use case |
|---|---|
| `scripts/live_stream_pipeline.py` | Real-time webcam or RTSP feed |
| `scripts/run_pipeline_a.py` | Offline analysis of a video file |

Both produce the same [Incident JSON contract](#incident-json-contract) and optionally send Telegram alerts.

---

## Live Stream Pipeline (event-driven)

```
Webcam / RTSP
      │
      ▼
PerceptionLayer              scripts/perception_layer.py
  - motion detection (frame diff)
  - person presence gate
  - cheap: no API call
      │
      │  activity_detected=True/False
      ▼
ActiveBufferManager          scripts/active_buffer_manager.py
  - rolling pre-roll ring buffer (default 2 s)
  - starts recording on activity_detected=True
  - stops after POST_ROLL_SECONDS of silence (default 3 s)
  - hard caps: MAX_EVENT_DURATION_SECONDS (18 s), MAX_SEGMENT_SIZE_BYTES (7 MB)
  - emits VideoSegment on close
      │
      │  VideoSegment(path, duration_seconds, frame_count)
      ▼
SegmentDispatcher            scripts/segment_dispatcher.py
  - bounded ThreadPoolExecutor (3 workers)
  - each worker runs Pipeline A end-to-end on one segment
      │
      ├── Stage 1: native_video_pipeline.py  (Nemotron)
      │     video → base64 frames → NVIDIA API → plain-text summary JSON
      │
      └── Stage 2: gemma_text_to_incident.py (Gemma)
            summary text → Google GenAI API → normalized Incident JSON
                │
      ┌─────────┴──────────┐
      ▼                    ▼
EvidenceManager      TelegramNotifier
keyframe JPEGs       alert with summary
data/evidence/       and evidence photo
      │
      ▼
IncidentStateManager         scripts/incident_state_manager.py
  - tracks open incidents across consecutive segments
  - merges overlapping incidents (same PPE item, same worker description)
  - writes live_incident_timeline.json on finalize
```

### Configuration constants (`live_stream_pipeline.py`)

| Constant | Default | Description |
|---|---|---|
| `TARGET_FPS` | 4 | Frames captured per second (Nemotron's sweet spot) |
| `RESOLUTION` | 1280×720 | Downscaled before encoding |
| `PRE_ROLL_SECONDS` | 2.0 | Buffer kept before an event starts |
| `POST_ROLL_SECONDS` | 3.0 | Extra frames captured after activity stops |
| `MIN_SEGMENT_SECONDS` | 1.5 | Segments shorter than this are discarded as noise |
| `MAX_EVENT_DURATION_SECONDS` | 18.0 | Long events are split; ISM stitches them back |
| `MAX_SEGMENT_SIZE_BYTES` | 7 MB | Hard size cap before rotation |
| `DISPATCH_MAX_WORKERS` | 3 | Parallel Pipeline A workers |

---

## Pipeline A — Video File Analysis

```
Video file (MP4 / AVI / ...)
      │
      ▼
Stage 1 — native_video_pipeline.py
  - reads video with OpenCV
  - samples at TARGET_FPS, downscales to RESOLUTION
  - compresses with ffmpeg if available (< 5 MB target)
  - sends to NVIDIA Nemotron via OpenAI-compatible API
  - receives plain-text temporal summary
  - saves: outputs/<dir>/nemotron_<stem>_summary.json
      │
      ▼
Stage 2 — gemma_text_to_incident.py
  - reads the Nemotron summary text
  - sends to Google Gemma via GenAI API with structured extraction prompt
  - parses response into normalized Incident JSON
  - saves: outputs/<dir>/<stem>_pipeline_a_incident.json
      │
      ▼ (optional)
send_notification_bot.py
  - reads the incident JSON
  - sends Telegram alert if incident_detected=True
```

### API models

| Stage | Model | Provider | Env var |
|---|---|---|---|
| Stage 1 | `nvidia/llama-3.2-90b-vision-instruct` (default) | NVIDIA build | `NVIDIA_NEMOTRON_MODEL` |
| Stage 2 | `gemma-4-26b-a4b-it` (default) | Google AI Studio | `--model` flag |

---

## Incident JSON Contract

Defined in `scripts/incident_contract.py`. Every pipeline output follows this schema:

```json
{
  "schema_version": "1.0",
  "video_id": "string",
  "source_pipeline": "nemotron_gemma",
  "models": ["nemotron", "gemma-4-26b-a4b-it"],
  "analysis_scope": ["hard_hat", "safety_vest", "safety_glasses", "gloves"],
  "incident_detected": true,
  "incidents": [
    {
      "incident_id": "uuid",
      "ppe_item": "hard_hat",
      "worker_description": "worker in orange vest near door",
      "start_time": 12.0,
      "end_time": 34.5,
      "duration_seconds": 22.5,
      "severity": "high",
      "frame_count": 90
    }
  ],
  "summary": "Human-readable summary of all detected incidents.",
  "quality": {
    "parse_success": true,
    "warnings": []
  }
}
```

The `incident_id` is a stable UUID. The live pipeline uses `<video_id>:<incident_id>` as a composite key for the API.

---

## FastAPI Backend

Entry point: `src/api/server.py` → `src/api/main.py`

Base URL: `http://localhost:8000`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness check |
| `GET` | `/api/cameras` | List all camera IDs with incident counts |
| `GET` | `/api/incidents` | All incidents across all cameras |
| `GET` | `/api/incidents/{camera_id}:{incident_id}` | Single incident detail |
| `GET` | `/api/settings/language` | Current UI language |
| `POST` | `/api/settings/language` | Set UI language (`en`, `ru`, `az`) |

Data is read from `outputs/live/<camera_id>/normalized_incident.json`. The backend is stateless — no database.

---

## Frontend Dashboard

`frontend/index.html` + `frontend/app.js` + `frontend/style.css`

Vanilla JS, no build step required. Served by any static file server or Python's `http.server`. Communicates with the FastAPI backend at `http://localhost:8000`.

Features: camera list, incident timeline, incident detail modal, language switcher (EN / RU / AZ).

---

## Data Flow Diagram

```
.env
 └─ NVIDIA_API_KEY ──► Stage 1 (Nemotron)
 └─ GOOGLE_API_KEY ──► Stage 2 (Gemma)
 └─ TELEGRAM_BOT_TOKEN ──► TelegramNotifier
 └─ CAMERA_SOURCE ──► live_stream_pipeline

Webcam/RTSP
 └─► PerceptionLayer ──► ActiveBufferManager
       └─► SegmentDispatcher
             ├─► Stage 1 + Stage 2
             │     └─► data/event_segments/<video_id>/
             │     └─► data/output_logs/<video_id>/live_incident_timeline.json
             ├─► EvidenceManager
             │     └─► data/evidence/<video_id>/
             └─► TelegramNotifier
                   └─► Telegram chat

FastAPI ──► outputs/live/<camera_id>/normalized_incident.json
Frontend ──► http://localhost:8000/api/*
```

---

## External Dependencies Boundary

| External service | Used by | Auth |
|---|---|---|
| NVIDIA build API (Nemotron) | `native_video_pipeline.py` | `NVIDIA_API_KEY` env var |
| Google AI Studio API (Gemma) | `gemma_text_to_incident.py` | `GOOGLE_API_KEY` env var |
| Telegram Bot API | `telegram_notifier.py`, `send_notification_bot.py` | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` |

All API keys are environment variables and must never be committed. See [`docs/ASSET_POLICY.md`](ASSET_POLICY.md).

---

## Failure Handling

- **NVIDIA API errors** (5xx, timeout, malformed response): logged, segment marked as failed, moved to `data/failed_segments/`. Pipeline continues.
- **Gemma parse failure**: logged with `quality.parse_success=false`, warnings attached to the incident JSON.
- **Camera disconnect**: `cap.read()` returns `False`, the loop sleeps 1 s and retries indefinitely.
- **Segment too short** (`< MIN_SEGMENT_SECONDS`): discarded as noise before dispatch.
- **Segment too large** (`> MAX_SEGMENT_SIZE_BYTES` or `> MAX_EVENT_DURATION_SECONDS`): rotated mid-event; IncidentStateManager stitches the resulting consecutive segments back into one logical incident.
- **Worker pool full**: `SegmentDispatcher.submit()` blocks until a worker is free (bounded queue).
