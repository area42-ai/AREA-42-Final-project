# Contributing to Watch Out

## Development Setup

```bash
git clone https://github.com/area42-ai/AREA-42-Final-project.git
cd AREA-42-Final-project

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
cp .env.example .env          # then fill in your API keys
```

## Git Workflow

All work happens in task branches — never directly on `main`.

```bash
git switch main
git pull --ff-only origin main
git switch -c <type>/<short-description>   # e.g. feat/multi-camera-support
```

Branch name prefixes:

| Prefix | Use |
|---|---|
| `feat/` | New feature |
| `fix/` | Bug fix |
| `chore/` | Tooling, deps, CI, docs |
| `test/` | Tests only |
| `refactor/` | Refactoring without behaviour change |

## Pull Requests

1. Open a PR against `main`.
2. Use the PR template (`.github/pull_request_template.md`).
3. Keep each PR to one logical change.
4. At least one team member must review before merge.
5. Squash-merge or regular merge — no rebase onto main.

## Code Standards

- Python 3.10+, follow existing style (no linter enforced yet).
- No secrets, videos, model weights, or generated outputs committed. See [`docs/ASSET_POLICY.md`](docs/ASSET_POLICY.md).
- Keep `scripts/` focused on pipeline logic; API code lives in `src/api/`.
- Add or update tests in `tests/` for non-trivial logic changes.

## Running Tests

```bash
python -m pytest tests/
```

## Commit Messages

Use the conventional commits format:

```
feat: add multi-camera support to live pipeline
fix: handle RTSP reconnect on dropped frames
chore: update requirements.txt
docs: rewrite ARCHITECTURE.md
```

One subject line (≤72 chars), imperative mood. Add a body for non-obvious reasoning.

## What Not to Commit

See [`docs/ASSET_POLICY.md`](docs/ASSET_POLICY.md) for the full list. Short version:

- `.env` (secrets)
- `data/raw/`, `data/test/`, `data/event_segments/`, `data/evidence/` (video/frames)
- `outputs/` (generated results)
- `models/` (weights)
- `.venv/`, `__pycache__/`, `*.pyc`
