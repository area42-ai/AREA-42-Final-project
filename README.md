<p align="center">
  <img src="assets/branding/watch-out-logo.png" alt="Watch Out Logo" width="220">
</p>

<h1 align="center">Watch Out</h1>
<p align="center">AI-powered workplace safety monitoring</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/NVIDIA-VLM_API-76b900?style=flat-square&logo=nvidia&logoColor=white" alt="NVIDIA">
  <img src="https://img.shields.io/badge/License-MIT-orange?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/Status-Active_Development-brightgreen?style=flat-square" alt="Status">
</p>

---

**Watch Out** monitors workplace video feeds and automatically detects PPE violations in real time. When a worker is missing required equipment for a sustained period, the system confirms the incident, saves evidence, and sends an alert — so safety supervisors are notified the moment a violation occurs, not after the fact.

Built by AREA-42 as a simplified VSS-style pipeline: frame sampling → NVIDIA-hosted VLM → incident logic → notifications.

---

## Current Status

| Component | Status | Notes |
|---|---|---|
| Frame extraction from video | ✅ Working | OpenCV, configurable interval |
| NVIDIA VLM inference | ✅ Working | Llama 3.2 11B Vision via API |
| Hard hat violation detection | ✅ Working | violation / compliant / uncertain |
| Temporal incident confirmation | ✅ Working | configurable consecutive-frame threshold |
| Evidence capture (frames + JSON) | ✅ Working | saved to `outputs/` |
| Live stream input | 🔧 In progress | RTSP / webcam |
| Notifications | 🔧 In progress | Telegram bot |
| LLM interpretation layer | 🔧 In progress | Gemma 4 via Ollama |
| General PPE classes | 📋 Planned | vests, gloves, goggles |
| Multi-person tracking | 📋 Planned | stable person IDs |
| Backend API | 📋 Planned | incident endpoints |
| Monitoring dashboard | 📋 Planned | supervisor UI |

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/area42-ai/AREA-42-Final-project.git
cd AREA-42-Final-project

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Open .env and add your NVIDIA_API_KEY

# 5. Run the pipeline on a video file
python scripts/video_frame_pipeline.py --video path/to/your/video.mp4
```

Output is saved to `outputs/<video_name>/`:

```
outputs/your_video/
├── frames/          # sampled JPEG frames
├── evidence/        # incident start and end frames
├── frame_results.json
├── raw_responses.json
└── incident.json
```

---

## Pipeline A — Quick Start

Pipeline A analyzes a whole video with **Nemotron** (plain-text temporal summary)
and then converts that text into a normalized incident JSON with **Gemma**. One
command runs both stages end-to-end.

**Never run this before? Do these three things first:**

1. **Activate the project virtual environment** (it already has OpenCV, the
   OpenAI SDK, and the Google GenAI SDK installed):

   ```powershell
   .\.venv\Scripts\Activate.ps1        # Windows PowerShell
   # source .venv/bin/activate         # macOS/Linux
   ```

2. **Create your `.env`** from the template and add your API keys:

   ```powershell
   copy .env.example .env              # Windows  (cp .env.example .env on macOS/Linux)
   ```

   Then open `.env` and set at least these two values:

   ```env
   NVIDIA_API_KEY=your_nvidia_api_key_here     # used by Stage 1 (Nemotron)
   GOOGLE_API_KEY=your_google_api_key_here     # used by Stage 2 (Gemma)
   ```

3. **Put your video in `data/test/`** (e.g. `data/test/worker_removes_helmet.mp4`).

**Run it (one line):**

```bash
python scripts/run_pipeline_a.py --video-name worker_removes_helmet.mp4 --output-dir outputs/pipeline_a
```

Optional flags: `--ppe-items hard_hat,safety_vest,safety_glasses,gloves` (defaults
to all four) and `--model <gemma-model>` (Stage 2 Gemma model; the Stage 1
Nemotron model comes from `NVIDIA_NEMOTRON_MODEL`).

**What you get:** on success the command prints exactly one line — the path to the
final normalized incident JSON — e.g.:

```
outputs/pipeline_a/worker_removes_helmet_pipeline_a_incident.json
```

That file follows the shared incident contract:

```json
{
  "schema_version": "1.0",
  "video_id": "worker_removes_helmet",
  "source_pipeline": "nemotron_gemma",
  "models": ["nemotron", "gemma-4-26b-a4b-it"],
  "analysis_scope": ["hard_hat", "safety_vest", "safety_glasses", "gloves"],
  "incident_detected": true,
  "incidents": [ /* one entry per confirmed missing PPE item */ ],
  "summary": "...",
  "quality": { "parse_success": true, "warnings": [] }
}
```

Alongside it, the intermediate Nemotron summary is saved as
`outputs/pipeline_a/nemotron_<video_stem>_summary.json`.

> If ffmpeg is not on your PATH, videos over 5 MB are sent uncompressed (slower
> and more costly) — the run still works. Errors (missing key, missing video,
> wrong environment) print a plain-language message and stop before any API call.

---

## Pipeline Architecture

```
Video file / live stream
        │
        ▼
 Frame Extraction (OpenCV)
        │
        ▼
 NVIDIA VLM API  ──►  violation / compliant / uncertain
        │
        ▼
 Temporal Incident Logic
        │
        ▼
 Evidence Capture ──► Notifications
```

The full architecture, API-first design decisions, and component boundaries are documented in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Evaluation Dataset

A manually annotated PPE video evaluation set (10 scenarios) is maintained externally in Google Drive, covering:

- Always compliant / always violating
- Worker removes and re-wears hard hat mid-video
- Two workers with mixed compliance
- Occlusion, low light, and difficult angles

Dataset access: [`data/README.md`](data/README.md)

---

## Documentation

| Document | Purpose |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Pipeline design and component boundaries |
| [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) | Product scope, confirmed vs. proposed decisions |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Official decision log |
| [`docs/MEETING_LOG.md`](docs/MEETING_LOG.md) | Meeting summaries |
| [`docs/TEAM_WORKFLOW.md`](docs/TEAM_WORKFLOW.md) | Git workflow and task management |
| [`docs/AI_WORKFLOW.md`](docs/AI_WORKFLOW.md) | How AI tools are used in this project |
| [`AGENTS.md`](AGENTS.md) | Instructions for AI coding agents |
| [`Plan.md`](Plan.md) | Dynamic roadmap and task tracker |

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
