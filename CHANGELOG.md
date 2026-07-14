# Changelog

All notable changes are documented here in reverse chronological order.

---

## [Unreleased]

- Multi-person tracking with stable IDs across frames
- Docker containerization
- Production deployment guide

---

## [0.5.0] — 2026-07

### Added
- Event-driven live stream pipeline (`scripts/live_stream_pipeline.py`)
  - `PerceptionLayer`: lightweight motion/person gate — no API call on idle frames
  - `ActiveBufferManager`: variable-length segments with pre-roll and post-roll
  - `SegmentDispatcher`: bounded 3-worker pool dispatching segments to Pipeline A
  - `IncidentStateManager`: cross-segment incident continuity and merging
  - `EvidenceManager`: keyframe JPEG extraction per incident
- Telegram notification system (`scripts/telegram_notifier.py`, `scripts/send_notification_bot.py`)
- FastAPI backend (`src/api/main.py`, `src/api/server.py`) with endpoints for cameras, incidents, language settings
- Web dashboard (`frontend/app.js`, `frontend/style.css`) — no build step, vanilla JS
- Windows one-click launcher (`start.bat`)
- `--camera` and `--video-id` CLI flags on live pipeline
- RTSP stream support alongside direct webcam capture

### Changed
- Frontend migrated from React/Vite to vanilla JS (removed build toolchain)
- `run_pipeline_a.py` extended with `--video-path`, `--camera-name`, `--skip-notification` flags
- `native_video_pipeline.py` updated with ffmpeg compression and resolution capping

---

## [0.4.0] — 2026-07

### Added
- Multi-worker PPE violation attribution — violations now attached to every visible worker, not just the first detected
- `scripts/extract_evidence_frames.py` for post-hoc keyframe extraction

### Fixed
- Nemotron API 500 errors caused by oversized frames (resolution now capped at 1280×720)
- Incident deduplication across segments

---

## [0.3.0] — 2026-06 (Pipeline A)

### Added
- Pipeline A end-to-end: Nemotron (Stage 1) + Gemma (Stage 2) in one command
- `scripts/incident_contract.py` — shared incident JSON schema v1.0
- `scripts/gemma_text_to_incident.py` — Gemma text-to-JSON extraction
- `scripts/native_video_pipeline.py` — Nemotron whole-video analysis
- `scripts/gemma_video_pipeline.py` — direct Gemma video pipeline (alternative)
- Nemotron vs Gemma benchmark comparison

---

## [0.2.0] — 2026-06 (Foundations)

### Added
- Frame extraction pipeline (`scripts/video_frame_pipeline.py`)
- NVIDIA VLM API integration (Llama 3.2 11B Vision)
- Temporal incident confirmation logic
- Evidence capture (frames + JSON) to `outputs/`
- Repository structure: `src/`, `scripts/`, `data/`, `docs/`, `tests/`, `configs/`
- Core documentation: ARCHITECTURE.md, PROJECT_CONTEXT.md, DECISIONS.md, AI_WORKFLOW.md, ASSET_POLICY.md
- `.env.example`, `.gitignore`, PR template

---

## [0.1.0] — 2026-06 (Project Kickoff)

### Added
- Initial repository setup
- Team identity: AREA-42, product name: Watch Out
- MIT License
- GitHub workflow: branches, PRs, no direct work on `main`
- Teacher-approved project direction: AI-powered PPE monitoring, API-first MVP
