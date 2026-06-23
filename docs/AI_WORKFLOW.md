# AI Workflow — Watch Out

How AREA-42 combines AI tools and human review. The goal is fast, repository-
aware work that stays honest and reviewable. See [`AGENTS.md`](../AGENTS.md) for
the shared agent rules.

## Mandatory task execution model

Every task follows this model (defined in Issue #16):

```text
GitHub Issue
  → Gemini acts as task coordinator and reviewer
  → Antigravity or Cursor acts as repository implementer
  → Gemini reviews implementation evidence
  → Gemini produces exact Git and Pull Request instructions
  → Human executes Git actions and approves the final result
```

- **Gemini** coordinates and reviews; it does not edit the repository or run Git.
- **Antigravity / Cursor** implement changes in the current task branch and
  return structured evidence; they never run Git.
- **The human** is the only actor who runs Git, opens the PR, and approves merge.

## Roles & responsibilities

### Gemini (task coordinator and reviewer)

Gemini must:

1. Receive the complete GitHub Issue text and the current branch name.
2. Restate the task and the expected deliverable.
3. Verify or propose the branch name.
4. Identify the relevant repository files.
5. Produce a step-by-step implementation plan.
6. Produce a complete prompt for Antigravity or Cursor.
7. Define the evidence required from the coding agent (see the completion report
   below).
8. Review the coding agent's completion report and terminal evidence.
9. Return exactly one of:
   - **`NOT READY`** — with a precise correction prompt for the coding agent; or
   - **`READY FOR COMMIT`** — with exact staging, commit, push, and PR
     instructions for the human.
10. Generate the PR title and description.
11. Include `Closes #<issue-number>` when the PR fully resolves the issue.
12. Never claim that code, tests, Git commands, or validation succeeded without
    actual supplied evidence.

### Antigravity / Cursor (repository implementer)

The coding agent must:

- work only in the current task branch;
- inspect the issue and the relevant repository files;
- make minimal, task-scoped changes;
- run the relevant checks;
- never commit, push, merge, rewrite history, or modify GitHub settings;
- return a structured **completion report** (see below).

### Human team member

The human must:

- create or switch to the task branch;
- provide the Issue to Gemini;
- pass Gemini's implementation prompt to the coding agent;
- return the coding agent's evidence to Gemini;
- inspect the final diff;
- execute the approved Git commands;
- open the Pull Request;
- respond to review feedback;
- approve merge only after review.

## Coding-agent completion report

Antigravity / Cursor must end every task with a report containing:

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

Gemini uses this report (plus real terminal evidence) to decide `NOT READY` vs
`READY FOR COMMIT`. Anything not backed by supplied evidence stays unverified.

## Task prompt template

Gemini uses this template when handing a task to a coding agent:

```text
Context:
  (What part of Watch Out this touches; relevant docs/files; issue number.)

Task:
  (What to do, specifically.)

Deliverable:
  (The exact files/output expected.)

Constraints:
  (Branch only; no commit/push; no invented facts; asset policy; minimal scope.)

Done when:
  (Clear, checkable completion criteria.)
```

## Git workflow (standard lifecycle)

The human executes these steps; Gemini supplies the exact commands after review:

```text
1.  git switch main
2.  git pull --ff-only origin main
3.  create a task branch        # git switch -c <type>/<short-description>
4.  implement through the coding agent
5.  review with Gemini          # NOT READY → correct; READY FOR COMMIT → continue
6.  stage specific files        # git add <specific paths>  (not git add -A)
7.  commit a logical unit       # git commit -m "<message>"
8.  push the task branch        # git push -u origin <branch>
9.  open a Draft PR if incomplete
10. mark Ready for review when complete
11. merge only after review
```

## Git & PR rules

- **No direct work on `main`.** Every change happens in a task branch.
- **Logical commits.** Each commit is one coherent, self-contained change with a
  clear message (commits are made by a human after review).
- **Stage specific files**, not everything, so unrelated changes are not swept in.
- **Regular pushes to task branches** so work is visible and backed up.
- **Draft Pull Requests** for work in progress; mark **Ready for review** when
  complete, get review, then merge.
- The PR follows [`.github/pull_request_template.md`](../.github/pull_request_template.md).

> AI agents prepare changes and evidence; humans perform commits, pushes, merges,
> and approvals.
