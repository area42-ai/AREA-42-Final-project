# Decisions Log

This file records important team decisions during the Final Project.

A decision should be documented here if it affects the project idea, dataset choice, team workflow, technical architecture, deadline, roles, presentation direction, or GitHub process.

---

## Decision Template

```text
Date:
Decision:
Reason:
Impact:
Owner:
```

---

## 2026-06-08 — Initial Team Setup

### Decision 1 — Daily Meeting Time

**Date:** 2026-06-08
**Decision:** The team will have a daily meeting around 21:00 ± 1 hour.
**Reason:** The team needs a fixed coordination rhythm to track progress, blockers, and next steps.
**Impact:** Each member should prepare a short daily update before the meeting.
**Owner:** Team 7

---

### Decision 2 — Temporary Roles

**Date:** 2026-06-08
**Decision:** Temporary team roles were created and discussed.
**Reason:** The team needs initial responsibility areas before the final project idea is selected.
**Impact:** Roles may be updated after the final idea and workload become clear.
**Owner:** Team 7

---

### Decision 3 — Dataset-First Approach

**Date:** 2026-06-08
**Decision:** The final project idea should not be locked before checking dataset availability and quality.
**Reason:** The teacher emphasized that a project without solid data is risky.
**Impact:** Every proposed idea should include at least one possible dataset and basic quality notes.
**Owner:** Team 7

---

### Decision 4 — GitHub Workflow Direction

**Date:** 2026-06-08
**Decision:** GitHub will be used for the project repository, documentation, branches, commits, and Pull Requests.
**Reason:** Contributions must be visible, reviewable, and organized.
**Impact:** Direct pushes to `main` should be avoided after the workflow is active. Team members should work through branches and Pull Requests.
**Owner:** Team 7

---

## 2026-06-09 — Project Management Environment

### Decision 5 — Core Management Files

**Date:** 2026-06-09
**Decision:** The team will use `Plan.md`, `docs/TEAM_WORKFLOW.md`, `docs/DECISIONS.md`, and `docs/MEETING_LOG.md` as the core management documentation.
**Reason:** The team needs a clear and transparent process that can be understood by all members and by the teacher.
**Impact:** Important progress, decisions, meeting outcomes, and workflow rules should be documented in GitHub, not only in Discord.
**Owner:** Elvin Nəsirov

---

### Decision 6 — MIT License

**Date:** 2026-06-09
**Decision:** The repository uses the MIT License.
**Reason:** MIT is simple, standard, and suitable for a student project.
**Impact:** The project code has a clear open-source license. Dataset licenses must still follow the original data providers.
**Owner:** AREA-42

---

### Decision 7 — Official Team Name

**Date:** 2026-06-09
**Decision:** The official team name is **AREA-42**. The previous "Team 7" name remains only as historical/class context.
**Reason:** The team needs a single, consistent official identity across the repository, documentation, and external materials.
**Impact:** README, Plan.md, and docs use AREA-42 as the current team name. "Team 7" is kept only where it refers to the original class/team number.
**Owner:** AREA-42

---

### Decision 8 — Management Strategy

**Date:** 2026-06-09
**Decision:** The team uses **Lightweight Scrumban with DRI Ownership**.
**Reason:** A lightweight Scrumban flow fits a small student team, and DRI ownership makes responsibility for each task unambiguous.
**Impact:** Tasks flow across a simple board with low WIP, each task has one Directly Responsible Individual, and `Done` requires an existing deliverable. Documented in docs/TEAM_WORKFLOW.md.
**Owner:** AREA-42

---

## 2026-06-21 — Project Direction (Internal Team Preference)

### Decision 9 — Internal Project Direction

**Date:** 2026-06-21
**Decision:** As an **internal team preference** (not yet teacher-approved), the team leans toward an **AI-Powered Workplace Safety Monitoring System** that analyzes video to detect PPE compliance, tracks people across frames, applies persistent-violation logic, captures incidents, and sends notifications through an API and monitoring UI.
**Reason:** The idea has a clear real-world problem (workplace safety), a feasible AI scope (PPE detection), and at least one candidate dataset (Roboflow PPE detection, CC BY 4.0).
**Impact:** The team prepares this direction for teacher review. No official approval is claimed on this date; the candidate dataset still needs quality validation before being locked.
**Owner:** AREA-42

---

## 2026-06-22 — Teacher Approval & Repository Restructure

### Decision 10 — Project Direction Approved by Teacher

**Date:** 2026-06-22
**Decision:** The teacher **approved** the selected project direction (AI-Powered Workplace Safety Monitoring) on 2026-06-22, making it the official final project.
**Reason:** The direction was reviewed and accepted as feasible and appropriate in scope.
**Impact:** Technical planning can begin. The architecture, MVP scope, and repository structure are documented in README.md.
**Owner:** AREA-42

### Decision 11 — Technical Repository Structure

**Date:** 2026-06-22
**Decision:** The repository is restructured into a planned technical layout: `src/` (with `video/`, `detection/`, `tracking/`, `rules/`, `incidents/`, `notifications/`, `api/`, `ui/`), plus `configs/`, `data/`, `models/`, `notebooks/`, `tests/`, `scripts/`, and `docs/`. Empty planned folders are kept with `.gitkeep`; `data/` and `models/` keep only a `README.md`.
**Reason:** Now that the direction is teacher-approved, the team needs a clear, agreed structure so each planned component has an owner and a home before implementation starts (GitHub Issue #11).
**Impact:** `.gitignore` was extended to exclude datasets, model weights/checkpoints, YOLO runs, uploaded videos, generated incident frames/clips, and local secrets. The previously committed PPE dataset was removed from Git tracking and now lives locally (git-ignored) under `data/raw/ppe_detection_v1/`. No datasets, weights, videos, outputs, or secrets are committed. All `src/` modules are placeholders and clearly labeled as planned, not implemented.
**Owner:** AREA-42
