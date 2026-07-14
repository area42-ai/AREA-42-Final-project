<p align="center">
  <img src="assets/branding/watch-out-logo.png" alt="Watch Out Logo" width="220">
</p>

<h1 align="center">Watch Out</h1>
<p align="center">AI-powered workplace safety monitoring</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/NVIDIA-Nemotron_VLM-76b900?style=flat-square&logo=nvidia&logoColor=white" alt="NVIDIA">
  <img src="https://img.shields.io/badge/Google-Gemma-4285F4?style=flat-square&logo=google&logoColor=white" alt="Google">
  <img src="https://img.shields.io/badge/License-MIT-orange?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/Status-Active_Development-brightgreen?style=flat-square" alt="Status">
</p>

---

**Watch Out** monitors workplace video feeds and automatically detects PPE violations in real time. When a worker is seen without required safety equipment, the system confirms the incident, saves evidence frames, and sends a Telegram alert — so supervisors are notified the moment a violation occurs, not after the fact.

Built by AREA-42 as an event-driven pipeline: webcam/RTSP feed → perception gate → NVIDIA Nemotron VLM → Gemma incident extraction → Telegram notification + web dashboard.

---

## System Status

| Component | Status | Notes |
|---|---|---|
| Frame extraction from video | ✅ Done | OpenCV, configurable FPS |
| NVIDIA Nemotron VLM inference | ✅ Done | Whole-video temporal summary via API |
| PPE detection (hard hat, vest, glasses, gloves) | ✅ Done | All four classes |
| Multi-worker attribution | ✅ Done | Violations attached per visible worker |
| Temporal incident confirmation | ✅ Done | Configurable pre/post-roll, min duration |
| Evidence capture (keyframes + JSON) | ✅ Done | Saved to `data/evidence/` |
| Gemma incident extraction (Stage 2) | ✅ Done | Plain-text summary → normalized JSON |
| Live stream input (RTSP / webcam) | ✅ Done | Event-driven, no fixed chunking |
| Telegram notifications | ✅ Done | Instant alerts with evidence |
| FastAPI backend | ✅ Done | `/api/cameras`, `/api/incidents`, `/api/settings/language` |
| Web dashboard (frontend) | ✅ Done | Vanilla JS, `frontend/` |
| Multi-person tracking | 📋 Planned | Stable person IDs across frames |
| Production deployment | 📋 Planned | Docker, HTTPS, auth |

---

## Quick Start

### Prerequisites

- Python 3.10+
- NVIDIA API key (for Nemotron) — [build.nvidia.com](https://build.nvidia.com)
- Google API key (for Gemma) — [aistudio.google.com](https://aistudio.google.com)
- Optional: Telegram bot token + chat ID for notifications

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/area42-ai/AREA-42-Final-project.git
cd AREA-42-Final-project

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell
# source .venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
copy .env.example .env          # Windows
# cp .env.example .env          # macOS / Linux
# Then fill in your API keys in .env
```

---

## Running the System

### Option A — Analyze a video file (Pipeline A)

Runs Nemotron whole-video analysis followed by Gemma incident extraction.

```bash
python scripts/run_pipeline_a.py \
  --video-name worker_removes_helmet.mp4 \
  --output-dir outputs/pipeline_a
```

Put your video in `data/test/` first. On success, prints the path to the final incident JSON.

Optional flags:
- `--ppe-items hard_hat,safety_vest,safety_glasses,gloves` — limit PPE scope
- `--model <gemma-model>` — override the Gemma model for Stage 2

### Option B — Live stream (webcam or RTSP)

Event-driven pipeline: captures only when activity is detected, dispatches segments to Pipeline A automatically.

```bash
# Webcam (index 0)
python scripts/live_stream_pipeline.py --camera 0 --video-id webcam

# RTSP stream
python scripts/live_stream_pipeline.py --camera rtsp://localhost:8554/test --video-id rtsp_cam
```

Press `Ctrl+C` to stop. The final timeline is saved to `data/output_logs/<video-id>/live_incident_timeline.json`.

### Option C — Web dashboard + API

```bash
# Windows: double-click or run
start.bat

# Manual (two terminals)
# Terminal 1 — backend
python src/api/server.py

# Terminal 2 — frontend
cd frontend && python -m http.server 5500
# Open http://localhost:5500 in your browser
```

---

## Pipeline Architecture

```
Webcam / RTSP / Video file
         │
         ▼
 Perception Layer          ← lightweight motion/person gate (cheap, no API call)
         │  event detected
         ▼
 Active Buffer Manager     ← variable-length event segments (pre-roll + post-roll)
         │  segment ready
         ▼
 Segment Dispatcher        ← bounded worker pool (3 workers)
         │
         ├─── Stage 1: NVIDIA Nemotron ──► plain-text temporal summary
         │
         └─── Stage 2: Google Gemma   ──► normalized Incident JSON
                                               │
                                  ┌────────────┴────────────┐
                                  ▼                         ▼
                       Evidence Manager            Telegram Notifier
                      (keyframe JPEGs)           (alert with evidence)
                                  │
                                  ▼
                      Incident State Manager
                      (cross-segment continuity)
                                  │
                                  ▼
                        FastAPI Backend  ──►  Web Dashboard
```

Full architecture details: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

---

## Incident JSON Contract

Every confirmed incident follows a shared schema (`scripts/incident_contract.py`):

```json
{
  "schema_version": "1.0",
  "video_id": "worker_removes_helmet",
  "source_pipeline": "nemotron_gemma",
  "models": ["nemotron", "gemma-4-26b-a4b-it"],
  "analysis_scope": ["hard_hat", "safety_vest", "safety_glasses", "gloves"],
  "incident_detected": true,
  "incidents": [
    {
      "incident_id": "...",
      "ppe_item": "hard_hat",
      "worker_description": "...",
      "start_time": 12.0,
      "end_time": 34.5,
      "duration_seconds": 22.5,
      "severity": "high"
    }
  ],
  "summary": "Worker removed hard hat at 12s and did not replace it.",
  "quality": { "parse_success": true, "warnings": [] }
}
```

---

## Project Structure

```
AREA-42-Final-project/
├── scripts/               # Core pipeline scripts
│   ├── live_stream_pipeline.py    # Entry point: live stream / webcam
│   ├── run_pipeline_a.py          # Entry point: video file analysis
│   ├── native_video_pipeline.py   # Stage 1: Nemotron VLM
│   ├── gemma_text_to_incident.py  # Stage 2: Gemma extraction
│   ├── perception_layer.py        # Motion/person gate
│   ├── active_buffer_manager.py   # Event-driven video buffering
│   ├── segment_dispatcher.py      # Worker pool for segment processing
│   ├── incident_state_manager.py  # Cross-segment incident continuity
│   ├── evidence_manager.py        # Keyframe evidence storage
│   ├── telegram_notifier.py       # Telegram alerts
│   └── send_notification_bot.py   # Standalone notification sender
├── src/api/               # FastAPI backend
│   ├── main.py            # App factory + all endpoints
│   ├── server.py          # Uvicorn entry point
│   └── camera_stream.py   # Camera streaming helpers
├── frontend/              # Web dashboard (vanilla JS)
│   ├── index.html
│   ├── app.js
│   └── style.css
├── docs/                  # Project documentation
├── data/                  # Local data (git-ignored except READMEs)
├── outputs/               # Pipeline outputs (git-ignored)
├── configs/               # Runtime configuration
├── assets/                # Branding
├── tests/                 # Test suite
├── .env.example           # Environment variable template
├── requirements.txt
└── start.bat              # Windows one-click launcher
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `NVIDIA_API_KEY` | ✅ | NVIDIA build API key (Nemotron, Stage 1) |
| `GOOGLE_API_KEY` | ✅ | Google AI Studio key (Gemma, Stage 2) |
| `TELEGRAM_BOT_TOKEN` | Optional | Telegram bot token for alerts |
| `TELEGRAM_CHAT_ID` | Optional | Chat/channel ID to send alerts to |
| `CAMERA_SOURCE` | Optional | Default camera: `0` (webcam) or RTSP URL |
| `NVIDIA_NEMOTRON_MODEL` | Optional | Override Nemotron model name |

---

## Evaluation Dataset

A manually annotated PPE video evaluation set (10 scenarios) is maintained in Google Drive, covering always-compliant, always-violating, helmet removal/replacement, two workers with mixed compliance, occlusion, low light, and difficult angles.

Dataset access: [`data/README.md`](data/README.md)

---

## Documentation

| Document | Purpose |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Full pipeline design and component reference |
| [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) | Product scope and confirmed decisions |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Official decision log |
| [`docs/AI_WORKFLOW.md`](docs/AI_WORKFLOW.md) | How AI tools are used in this project |
| [`docs/ASSET_POLICY.md`](docs/ASSET_POLICY.md) | What is and isn't committed to Git |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How to contribute |
| [`AGENTS.md`](AGENTS.md) | Instructions for AI coding agents |

---

## Team

**AREA-42** · Data & AI Cohort 2026

- Elvin Nəsirov
- Roya Nasirova
- Adil Hasanov
- Aysu Mammadova Anar

[GitHub Organization](https://github.com/area42-ai) · [Project Board](https://github.com/orgs/area42-ai/projects/1/views/1)

---

## License

This project is licensed under the [MIT License](LICENSE).
