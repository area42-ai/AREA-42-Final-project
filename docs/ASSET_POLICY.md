# Asset Policy — Watch Out

This document defines what may and may not be committed to Git, and where large
or sensitive assets should live instead. It complements the project
[`.gitignore`](../.gitignore).

**Core rule:** large or sensitive assets must remain **outside Git**. Code,
documentation, small configs, and small metadata files belong in Git; media,
datasets, weights, secrets, and generated outputs do not.

## Asset rules

| Asset | Commit to Git? | Where it lives instead |
| ----- | -------------- | ---------------------- |
| Test videos | No | `data/test/` locally; shared via Google Drive / approved external storage |
| Demo videos | No | `assets/demo/` locally; shared via Google Drive / approved external storage |
| Raw datasets | No | `data/raw/` locally; downloaded manually per `data/README.md` |
| Model weights / checkpoints | No | `models/weights/` locally; shared via release asset or external storage |
| API keys / secrets | No | Environment variables / `.env` (git-ignored); never in code or docs |
| Generated evidence clips / frames | No | `outputs/` locally (or runtime path); shared externally if needed |
| Screenshots | Generally no | `assets/demo/` or external storage; avoid committing large image sets |
| Logs and API responses | No | Local logs / `outputs/`; never commit responses with sensitive content |
| Virtual environments and caches | No | Local only (e.g. `.venv/`, `__pycache__/`, tool caches) |

> Small, non-sensitive illustrative images for documentation may be committed at
> the team's discretion, but media used as test/demo data must stay out of Git.

## Proposed local locations

These are the proposed local paths. They do **not** all need to be created now;
create them when a task actually needs them.

- `data/raw/` — raw datasets (local only).
- `data/test/` — small evaluation / test media (local only).
- `assets/demo/` — demo videos and demo media (local only).
- `outputs/` — generated clips, frames, and run outputs (local only).
- `models/weights/` — model weights / checkpoints (local only).

## Shared media

- Shared test and demo media should be stored in **Google Drive** or another
  **approved external storage**.
- It should be retrieved **manually**, or later through a helper script
  (a fetch script is a future, optional addition — not required now).
- Never commit the media itself or any download tokens / API keys.

## Evaluation set

Even though the MVP uses an **external NVIDIA model via API** (not a custom
trained model), a **small evaluation set is still required**:

- it lets the team sanity-check the model's behavior on representative footage;
- it makes demos reproducible and supports basic, honest claims about behavior;
- it stays small and lives outside Git (e.g. `data/test/` + external storage).

A full/large training dataset is **not** a required dependency for the current
MVP (see `docs/PROJECT_CONTEXT.md`).
