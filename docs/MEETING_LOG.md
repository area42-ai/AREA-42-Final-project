# Meeting Log

This file records short summaries of AREA-42 (formerly Team 7) meetings during the Final Project.

Each meeting summary should include the date, participants, main topics, completed items, decisions, blockers, and next steps.

---

## Meeting Template

```text
Date:
Participants:
Main topics:
Completed:
Decisions:
Blockers:
Next steps:
```

---

## 2026-06-08 — Initial Coordination Meeting

### Participants

* Roya Nasirova
* Adil Hasanov
* Elvin Nəsirov
* Aysu Mammadova Anar

### Main Topics

* Teacher guidelines
* Temporary team roles
* Daily meeting time
* Initial tasks
* GitHub usage
* Dataset-first project selection

### Completed

* Teacher guidelines were explained and discussed.
* Temporary roles were created and discussed.
* Daily meeting time was agreed: 21:00 ± 1 hour.
* Initial tasks were assigned.
* GitHub was selected as the main repository and documentation platform.

### Decisions

* Daily meeting time: 21:00 ± 1 hour.
* Temporary roles are active but may change later.
* Final project idea should not be selected before checking dataset quality.
* GitHub will be used for repository, documentation, branches, commits, and Pull Requests.

### Blockers

* Final project idea is not selected yet.
* Dataset availability and quality are not confirmed yet.
* GitHub Project board still needs to be created.
* Team name is not finalized yet.

### Next Steps

* Discuss possible project ideas.
* Research possible datasets.
* Create GitHub Project board.
* Create and maintain `Plan.md`.
* Document decisions and meeting summaries in GitHub.
* Finalize team name and project idea by the end of the week.

---

## 2026-06-09 — Management Environment Setup

### Participants

* Elvin Nəsirov

### Main Topics

* GitHub repository setup
* Project documentation structure
* Team workflow documentation
* Task tracking environment

### Completed

* Repository created.
* README.md created.
* Python `.gitignore` added.
* MIT License added.
* `Plan.md` created.
* `docs/TEAM_WORKFLOW.md` created.
* `docs/DECISIONS.md` created.
* `docs/MEETING_LOG.md` created.

### Decisions

* Official team name confirmed: AREA-42 (formerly Team 7).
* Management strategy confirmed: Lightweight Scrumban with DRI Ownership.
* GitHub documentation will be used as the official project management record.
* Discord will be used for fast communication and daily coordination.
* GitHub Project will be used as the official task board.

### Blockers

* GitHub Project board still needs to be created.
* Initial GitHub Project tasks need to be added.
* Team members need access to the repository and project board.

### Next Steps

* Create GitHub Project board.
* Add initial tasks to the board.
* Update `Plan.md`.
* Update Discord `#important-links`.
* Announce that the basic management environment is ready.

---

## 2026-06-21 — Project Idea Discussion (Internal Preference)

### Participants

* Roya Nasirova
* Adil Hasanov
* Elvin Nəsirov
* Aysu Mammadova Anar

### Main Topics

* Review of candidate project ideas
* Dataset availability for each idea
* Feasibility and scope discussion
* Team's internal project direction

### Completed

* Candidate ideas were compared on problem value, feasibility, and data availability.
* A candidate PPE detection dataset (Roboflow, CC BY 4.0) was identified.
* The team agreed on an internal preference (not yet teacher-approved).

### Decisions

* Internal team preference: **AI-Powered Workplace Safety Monitoring System** (see DECISIONS.md, Decision 9). This is a team preference, not an official approval.
* The MVP will cover the end-to-end pipeline on a single video source.
* The candidate PPE dataset still needs quality validation before being locked.

### Blockers

* Project direction not yet approved by the teacher.
* Dataset quality is not fully validated yet.
* Repository is not yet structured for technical work.

### Next Steps

* Present the direction to the teacher for approval.
* Prepare to restructure the repository for technical work.
* Validate the candidate dataset.

---

## 2026-06-22 — Teacher Approval & Repository Restructure

### Participants

* AREA-42

### Main Topics

* Teacher approval of the project direction
* Technical repository structure
* Project documentation updates
* `.gitignore` rules for data, models, runs, videos, outputs, and secrets

### Completed

* The teacher **approved** the project direction (AI-Powered Workplace Safety Monitoring) on 2026-06-22.
* Repository restructured into the planned technical layout (`src/` modules, `configs/`, `data/`, `models/`, `notebooks/`, `tests/`, `scripts/`, `docs/`).
* `README.md` rewritten with problem, solution, MVP scope, architecture, structure, and placeholders.
* `Plan.md` updated to the teacher-approved project status.
* `.gitignore` extended for datasets, model weights/checkpoints, YOLO runs, uploaded videos, generated incident frames/clips, and local secrets.
* Previously committed PPE dataset removed from Git tracking; it now lives locally (git-ignored) under `data/raw/ppe_detection_v1/`.

### Decisions

* Project direction approved by the teacher (see DECISIONS.md, Decision 10).
* Technical repository structure approved (see DECISIONS.md, Decision 11).
* All `src/` components are placeholders, clearly labeled as planned, not implemented.

### Blockers

* Candidate dataset validation still ongoing.
* Component DRIs (owners) not assigned yet.

### Next Steps

* Validate the candidate PPE dataset.
* Assign a DRI to each planned `src/` component.
* Add the GitHub Project board link to documentation.
* Begin MVP implementation (video input + PPE detection first).
