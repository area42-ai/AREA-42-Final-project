# AGENTS.md — Instructions for AI Coding Agents

This is the main, platform-independent instruction file for any AI coding agent
or assistant working in this repository (Cursor, Antigravity, Gemini, Codex, and
others). Read this file first, before making any change.

## 1. Project & team identity

- **Team:** AREA-42 (formerly Team 7).
- **Product name:** **Watch Out** — an AI-powered workplace safety monitoring
  system that analyzes video to detect PPE / safety violations and surface them
  as timestamped evidence.
- **Status:** technical planning; the current technical direction is
  **API-first** (see `docs/PROJECT_CONTEXT.md`).

## 2. Source of truth

- The repository documentation is the source of truth for code, tasks,
  decisions, and project context.
- GitHub is the canonical home for code, tasks, decisions, and documentation.
- Start from these documents and keep them consistent:
  - [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) — product, scope, confirmed/proposed/TBD.
  - [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — proposed API-first pipeline.
  - [`docs/ASSET_POLICY.md`](docs/ASSET_POLICY.md) — what may and may not be committed.
  - [`docs/AI_WORKFLOW.md`](docs/AI_WORKFLOW.md) — how AI tools and humans collaborate.
  - [`docs/DECISIONS.md`](docs/DECISIONS.md) — historical decision log.
  - [`README.md`](README.md) and [`Plan.md`](Plan.md) — overview and roadmap.

## 3. Before editing

- Inspect the repository: read the relevant files and understand the existing
  structure and conventions before changing anything.
- Identify existing information that must be preserved. Do not rewrite working
  documentation unnecessarily.

## 4. Git boundaries (hard rules)

- Work **only in the current task branch**.
- **Never** make direct changes to `main`.
- **Do not** commit, push, merge, delete branches, or rewrite Git history.
- Stop before commit and push so a human can review.
- Do not modify unrelated files without explicit human approval.

## 5. Accuracy rules (do not invent)

- Do not invent metrics, API behavior, model capabilities, dataset facts, costs,
  supported event/violation classes, or completed work.
- The exact NVIDIA model, endpoint, capabilities, pricing, and API limits are
  **TBD** unless already confirmed in the repository. Keep them marked as TBD.
- Use **TBD** for genuinely unknown information rather than guessing.
- The logo is being finalized by the team; do not invent or generate a logo.

## 6. Asset rules (do not commit)

Never commit any of the following (see [`docs/ASSET_POLICY.md`](docs/ASSET_POLICY.md)):

- raw datasets, training datasets, or annotations;
- videos (test, demo, uploaded) and generated clips/frames;
- model weights or checkpoints;
- API keys, secrets, or API responses containing sensitive information;
- virtual environments, caches, and temporary files;
- training/experiment outputs or other large binaries.

Large or sensitive assets live outside Git (e.g. Google Drive or another
approved external storage).

## 7. How to change code & docs

- Make **minimal, task-scoped** changes. Do only what the task asks.
- Preserve existing conventions (file structure, naming, doc style, headings).
- Do not create application code unless the task explicitly asks for it.

## 8. Verification

- Run the checks relevant to your change (e.g. linters, tests, link checks,
  `git status`, `git diff --check`, `git diff --stat`).
- Confirm no dataset, video, secret, binary, or generated output was added.

## 9. Task execution model

AREA-42 uses a mandatory task execution model (see
[`docs/AI_WORKFLOW.md`](docs/AI_WORKFLOW.md)):

```text
GitHub Issue → Gemini coordinates → Antigravity/Cursor implements
  → Gemini reviews evidence → Gemini produces exact Git/PR instructions
  → Human executes Git and approves
```

As the coding agent, you implement in the current task branch and return a
structured completion report. You never run Git or modify GitHub settings.

## 10. Reporting (end of task)

Always end with a structured **completion report** containing:

```text
Issue addressed:
Files created:
Files modified:
Files deleted:
Implementation summary:
Commands executed:
Exact validation results:
Git diff summary:
Limitations:
Unverified assumptions:
Remaining work:
Recommended commit scope:
```

Anything not backed by real terminal evidence must be marked as unverified.
Then **stop and hand off to a human for commit and push** (after Gemini review).
