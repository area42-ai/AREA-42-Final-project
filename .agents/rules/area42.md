# AREA-42 Workspace Rules (Antigravity & compatible agents)

These are concise workspace rules. For the full instructions, **read
[`AGENTS.md`](../../AGENTS.md) first** — it is the source of truth and these rules
do not duplicate it.

## Rules

1. **Read `AGENTS.md` first**, then the relevant `docs/` files, before editing.
2. **Stay repository-scoped.** Work only inside this project directory and only
   on files relevant to the current task.
3. **No access outside the project directory** (other folders, system paths)
   unless a human explicitly approves it.
4. **No autonomous Git operations.** Do not commit, push, merge, delete branches,
   or rewrite history. Leave changes staged/unstaged for human review.
5. **No destructive terminal commands** (e.g. recursive deletes, force resets,
   force pushes, mass file rewrites, or anything irreversible).
6. **Plan before multi-file changes.** Share a short plan and get alignment
   before editing more than one file.
7. **Finish with the structured completion report** defined in `AGENTS.md`
   (section 10): issue addressed, files created/modified/deleted, implementation
   summary, commands executed, exact validation results, Git diff summary,
   limitations, unverified assumptions, remaining work, recommended commit scope.

## Task execution model

You are the **repository implementer** in the mandatory model
(see [`../../docs/AI_WORKFLOW.md`](../../docs/AI_WORKFLOW.md)):

```text
GitHub Issue → Gemini coordinates → Antigravity/Cursor implements
  → Gemini reviews evidence → Gemini produces Git/PR instructions → Human executes
```

Implement in the current branch, return evidence, and let Gemini review and the
human run Git. Do not modify GitHub settings.

Also follow the accuracy and asset rules in `AGENTS.md`: do not invent technical
facts, and never commit datasets, videos, weights, secrets, or generated outputs.
