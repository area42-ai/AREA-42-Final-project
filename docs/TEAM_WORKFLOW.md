# Team Workflow

This document explains how AREA-42 (formerly Team 7) organizes communication, task tracking, decisions, documentation, and GitHub workflow during the Final Project.

The goal is to make the project process clear for all team members and understandable for the teacher.

---

## 0. Team Management Strategy

AREA-42 uses **Lightweight Scrumban with DRI Ownership**.

* **Scrumban** — a mix of Scrum and Kanban. We keep a short daily standup (Scrum rhythm) and a simple board with task columns and flow (Kanban). There are no heavy sprints; tasks move continuously across the board.
* **DRI (Directly Responsible Individual)** — every task has exactly one person who is directly responsible for it. The DRI may ask others for help, but they own the task's progress, blockers, and deliverable.
* **WIP limit** — Work In Progress is kept low. Each member should keep only a small number of tasks `In Progress` at once so work actually gets finished instead of piling up.
* **Done means deliverable exists** — a task is only `Done` when its deliverable actually exists and is visible in GitHub (a file, a PR, a board update, etc.). "Almost done" or "discussed" is not `Done`.

---

## 1. Main Tools

| Tool                | Purpose                                                     |
| ------------------- | ----------------------------------------------------------- |
| Discord             | Daily communication, announcements, quick updates, blockers |
| GitHub Repository   | Code, documentation, project files, version history         |
| GitHub Project      | Task tracking and progress board                            |
| Plan.md             | Dynamic roadmap, current tasks, owners, deadlines, blockers |
| docs/DECISIONS.md   | Official project decisions and reasons                      |
| docs/MEETING_LOG.md | Meeting summaries and next steps                            |

---

## 2. Discord Usage

Discord is used for fast communication and short updates.

| Channel             | Purpose                                                                           |
| ------------------- | --------------------------------------------------------------------------------- |
| #announcements      | Important team-wide updates only                                                  |
| #important-links    | Links to repository, Plan.md, project board, datasets, presentation, final report |
| #teacher-guidelines | Teacher requirements and project rules                                            |
| #daily-standup      | Daily progress updates                                                            |
| #tasks              | Short task updates before they are moved into Plan.md or GitHub Project           |
| #decisions-log      | Important team decisions                                                          |
| #github-and-prs     | Repository updates, branches, commits, Pull Requests                              |
| #ideas-and-data     | Project ideas, datasets, and feasibility research                                 |

### Discord Rule

If something is only a quick update, it can stay in Discord.
If it affects the project roadmap, task ownership, deadline, or final decision, it should also be documented in GitHub.

---

## 3. Daily Meeting

Daily meeting time:

```text
21:00 ± 1 hour
```

Each member should prepare a short update:

```text
Yesterday:
Today:
Blockers:
Need help from:
```

### Example

```text
Yesterday: I researched two possible datasets.
Today: I will check dataset quality and possible target variables.
Blockers: I am not sure if the dataset has enough useful features.
Need help from: Data member.
```

---

## 4. Task Management

Tasks should be tracked in two places:

| Place          | Usage                                        |
| -------------- | -------------------------------------------- |
| Discord #tasks | Fast task updates and temporary coordination |
| GitHub Project | Official task board                          |
| Plan.md        | High-level task summary and roadmap          |

Every important task should have:

* Task name
* Owner
* Status
* Deadline
* Deliverable
* Notes or blockers

### Task Statuses

Use these statuses:

```text
Backlog
Todo
In Progress
Blocked
Review
Done
```

### Task Template

```text
Task:
Owner:
Status:
Deadline:
Deliverable:
Notes:
```

---

## 5. Plan.md Usage

`Plan.md` is the dynamic project management file.

It should answer:

* What are we working on?
* Who owns each task?
* What is done?
* What is blocked?
* What is next?

`Plan.md` should be updated when:

* A new task is assigned
* A task status changes
* A blocker appears
* A blocker is solved
* A project idea is added
* A dataset is found
* A deadline changes
* A major next step changes

---

## 6. Decision Management

Important decisions should be written in:

```text
docs/DECISIONS.md
```

A decision should be documented when it affects:

* Project idea
* Dataset choice
* Technical architecture
* Model choice
* Team roles
* Deadline
* Presentation direction
* GitHub workflow

### Decision Template

```text
Date:
Decision:
Reason:
Impact:
Owner:
```

### Example

```text
Date: 2026-06-08
Decision: The team will not lock the final project idea before checking dataset quality.
Reason: The teacher emphasized that a project without solid data is risky.
Impact: Every proposed idea should include at least one possible dataset.
Owner: Team 7
```

---

## 7. Meeting Log

Meeting summaries should be written in:

```text
docs/MEETING_LOG.md
```

Each meeting summary should include:

* Date
* Participants
* Main topics
* Completed items
* Decisions
* Next steps
* Blockers

### Meeting Log Template

```text
Date:
Participants:
Main topics:
Completed:
Decisions:
Next steps:
Blockers:
```

---

## 8. GitHub Workflow

No one should push directly to the `main` branch after the workflow is active.

For each technical or documentation task:

1. Create a new branch.
2. Make changes.
3. Commit the changes.
4. Push the branch.
5. Open a Pull Request.
6. Request review from at least one teammate.
7. Merge only after review.

### Branch Naming

Use clear branch names:

```text
docs/update-plan
docs/add-meeting-log
data/research-datasets
detection/ppe-baseline
tracking/person-tracker
rules/persistent-violation
incidents/capture-frames
notifications/alerts
api/create-endpoints
ui/monitoring-layout
```

Branch prefixes should match the planned components in `src/` where possible
(for example `detection/...`, `tracking/...`, `rules/...`, `api/...`, `ui/...`).

### Commit Message Examples

```text
Add initial project plan
Update team workflow documentation
Add meeting log for 2026-06-08
Add dataset research notes
Update task status in Plan.md
```

---

## 9. Pull Request Rule

A Pull Request should explain:

* What was changed
* Why it was changed
* What needs review
* Whether there are blockers

### Pull Request Template

```text
## Summary

Briefly describe what changed.

## Why

Explain why this change is needed.

## Checklist

- [ ] I updated related documentation if needed
- [ ] I checked that the file is readable
- [ ] I requested review from a teammate

## Notes

Add any extra notes or blockers here.
```

---

## 10. Documentation Rule

Use this rule:

| Situation                     | Where to document                 |
| ----------------------------- | --------------------------------- |
| Quick update                  | Discord                           |
| Important team-wide update    | Discord #announcements            |
| Current task progress         | Discord #tasks + GitHub Project   |
| High-level roadmap            | Plan.md                           |
| Official decision             | docs/DECISIONS.md                 |
| Meeting summary               | docs/MEETING_LOG.md               |
| Code/documentation change     | GitHub commit + Pull Request      |
| Final explanation for teacher | README.md + docs/TEAM_WORKFLOW.md |

---

## 11. Current Workflow Summary

The team workflow is:

1. Discuss in Discord.
2. Track tasks in GitHub Project.
3. Keep high-level progress in Plan.md.
4. Record major decisions in docs/DECISIONS.md.
5. Record meeting summaries in docs/MEETING_LOG.md.
6. Use branches and Pull Requests for GitHub changes.
7. Keep all important work visible and reviewable.

---

## 12. Repository Structure

Now that the project idea is approved (AI-Powered Workplace Safety Monitoring),
the repository is organized into a planned technical layout. The `src/` modules
are **placeholders** until implementation begins.

| Path                 | Purpose                                              |
| -------------------- | --------------------------------------------------- |
| `src/video/`         | Video input / frame reading (planned)               |
| `src/detection/`     | PPE & person detection (planned)                    |
| `src/tracking/`      | Person tracking across frames (planned)             |
| `src/rules/`         | Violation & persistent-violation logic (planned)    |
| `src/incidents/`     | Incident capture (frames/clips + metadata) (planned) |
| `src/notifications/` | Alerts / notifications (planned)                    |
| `src/api/`           | Backend API (planned)                               |
| `src/ui/`            | Monitoring UI (planned)                             |
| `configs/`           | Configuration files (planned)                       |
| `data/`              | Local datasets (git-ignored; see `data/README.md`)  |
| `models/`            | Model weights/checkpoints (git-ignored; see `models/README.md`) |
| `notebooks/`         | Exploration & experiments (planned)                 |
| `tests/`             | Automated tests (planned)                           |
| `scripts/`           | Helper / utility scripts (planned)                  |
| `docs/`              | Project & team documentation                        |

Datasets, model weights, videos, runtime outputs, and secrets are **not**
committed; see [`.gitignore`](../.gitignore). A full description of the project
lives in [`README.md`](../README.md).

---

## 13. Maintenance

This document should be updated when the team changes its workflow, tools, or project management rules.
