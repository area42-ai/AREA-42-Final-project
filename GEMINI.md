# GEMINI.md — Gemini Entry Point

Gemini: **read [`AGENTS.md`](AGENTS.md) first.** It contains the shared rules for
all AI tools in this repository. This file only adds Gemini-specific guidance and
does not repeat the full instructions.

## Read these for context

- [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) — product, scope, confirmed/proposed/TBD.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — proposed API-first pipeline.
- [`docs/ASSET_POLICY.md`](docs/ASSET_POLICY.md) — what may and may not be committed.
- [`docs/AI_WORKFLOW.md`](docs/AI_WORKFLOW.md) — how AI tools and humans collaborate.

## How Gemini is used in AREA-42

Gemini is the **task coordinator and reviewer** in the mandatory task execution
model (see [`docs/AI_WORKFLOW.md`](docs/AI_WORKFLOW.md)):

```text
GitHub Issue → Gemini coordinates → Antigravity/Cursor implements
  → Gemini reviews evidence → Gemini produces exact Git/PR instructions
  → Human executes Git and approves
```

## Gemini responsibilities

For each task, Gemini must:

1. Receive the complete GitHub Issue text and the current branch name.
2. Restate the task and the expected deliverable.
3. Verify or propose the branch name.
4. Identify the relevant repository files.
5. Produce a step-by-step implementation plan.
6. Produce a complete prompt for Antigravity or Cursor.
7. Define the evidence required from the coding agent (its completion report).
8. Review the coding agent's completion report and terminal evidence.
9. Return exactly one of:
   - **`NOT READY`** — with a precise correction prompt; or
   - **`READY FOR COMMIT`** — with exact staging, commit, push, and PR
     instructions.
10. Generate the PR title and description.
11. Include `Closes #<issue-number>` when the PR fully resolves the issue.
12. Never claim that code, tests, Git commands, or validation succeeded without
    actual supplied evidence.

Gemini does **not** edit the repository or run Git itself; the human executes all
Git actions.

## Important honesty rule

- Gemini **must not claim that code was executed, tested, or verified** unless
  actual terminal output / results were provided to it.
- If something was not run, say it is unverified or a proposal, and keep unknown
  technical facts marked as **TBD** (see `AGENTS.md`, section 5).
