# AREA-42 Final Project Plan

This file is the dynamic project plan for AREA-42 (formerly Team 7).
It tracks the current project status, team decisions, tasks, owners, deadlines, blockers, and next steps.

---

## 1. Team Information

### Team Members

* Roya Nasirova
* Adil Hasanov
* Elvin Nəsirov
* Aysu Mammadova Anar

### Current Status

| Item                        | Status                                            |
| --------------------------- | ------------------------------------------------- |
| Team name                   | AREA-42                                           |
| Final project idea          | AI-Powered Workplace Safety Monitoring (teacher-approved 2026-06-22) |
| Project phase               | Technical planning (implementation not started)   |
| Daily meeting time          | 21:00 ± 1 hour                                    |
| GitHub repository           | Created                                           |
| GitHub Project board        | Created (insert URL manually — see Links)         |
| Team roles                  | Temporary roles discussed                         |
| Project management strategy | Lightweight Scrumban with DRI Ownership           |

### Current Setup Status

The project direction was the team's internal preference, and was
**approved by the teacher on 2026-06-22**. The repository has been restructured
for technical work. Implementation of the pipeline has **not** started yet — the
`src/` modules are planned placeholders.

* Done: GitHub repository, README, .gitignore, MIT License
* Done: Plan.md, docs/TEAM_WORKFLOW.md, docs/DECISIONS.md, docs/MEETING_LOG.md
* Done: Official team name (AREA-42) and management strategy (Lightweight Scrumban with DRI Ownership)
* Done: GitHub Project board created (link TBD)
* Done: Project direction approved by the teacher on 2026-06-22 — AI-Powered Workplace Safety Monitoring
* Done: Repository restructured into planned technical layout (`src/`, `configs/`, `data/`, `models/`, `notebooks/`, `tests/`, `scripts/`, `docs/`)
* Pending: Candidate dataset validation, technical implementation

### External Resources & Links

| Resource              | Status / Link                                                                |
| --------------------- | --------------------------------------------------------------------------- |
| GitHub Project Board  | `https://github.com/orgs/area42-ai/projects/1/views/1`               |
| Discord important links | TBD                                                                       |
| Candidate dataset     | PPE detection (Roboflow, CC BY 4.0) — under validation; see `data/README.md` |
| Presentation          | TBD                                                                         |
| Final report          | TBD                                                                         |
| Demo video            | TBD                                                                         |

---

## 2. Main Teacher Guidelines

The team should follow these project management and technical workflow rules:

* Finalize the team name, project idea, and management strategy by the end of the week.
* Do not rush the project idea.
* Check dataset availability and quality before choosing the final idea.
* Each team member should have a clear role and visible contribution.
* Use GitHub for project files, documentation, code, branches, commits, and Pull Requests.
* Avoid direct pushes to the `main` branch.
* Use branches and Pull Requests for task-based work.
* Review teammates’ work before merging.
* Track tasks, owners, progress, and blockers in this file.

---

## 3. Working Rules

### Communication

* Discord is used for daily communication, announcements, task updates, and quick coordination.
* Important decisions should be written down in the decision log.
* Daily meetings should happen around 21:00 ± 1 hour.

### Task Management

Every task should include:

* Task name
* Owner
* Status
* Deadline
* Deliverable
* Notes or blockers

### GitHub Workflow

For each technical or documentation task:

1. Create a new branch.
2. Make changes.
3. Commit the changes.
4. Push the branch.
5. Open a Pull Request.
6. Request review from at least one teammate.
7. Merge only after review.

---

## 4. Immediate Action Items

| Task                           | Owner          | Status      | Deadline    | Deliverable                      | Notes                                            |
| ------------------------------ | -------------- | ----------- | ----------- | -------------------------------- | ------------------------------------------------ |
| Explain teacher guidelines     | Elvin          | Done        | 2026-06-08  | Guidelines explained to the team | Completed during initial meeting                 |
| Decide temporary roles         | AREA-42        | Done        | 2026-06-08  | Temporary roles discussed        | Roles may change after idea selection            |
| Agree on daily meeting time    | AREA-42        | Done        | 2026-06-08  | Daily meeting time selected      | 21:00 ± 1 hour                                   |
| Assign initial tasks           | Elvin / AREA-42 | Done       | 2026-06-08  | First tasks assigned             | Initial coordination completed                   |
| Discuss possible project ideas | All members    | Done        | 2026-06-21  | 1–2 project ideas per member     | Ideas discussed; team's internal preference was safety monitoring |
| Check dataset availability     | All members    | In Progress | TBD         | Dataset links and quality notes  | Candidate PPE dataset found; quality validation ongoing |
| Create GitHub repository       | Elvin          | Done        | 2026-06-09  | Repository created               | README, Python .gitignore, and MIT License added |
| Create Plan.md                 | Elvin          | Done        | 2026-06-09  | Dynamic project plan             | This file will be updated regularly              |
| Create team workflow documentation | Elvin      | Done        | 2026-06-09  | docs/TEAM_WORKFLOW.md            | Workflow and management strategy documented      |
| Create decisions log           | Elvin          | Done        | 2026-06-09  | docs/DECISIONS.md                | Official decisions recorded                      |
| Create meeting log             | Elvin          | Done        | 2026-06-09  | docs/MEETING_LOG.md              | Meeting summaries recorded                       |
| Create GitHub Project board    | AREA-42        | Done        | 2026-06-09  | Task board                       | Board created; link to be added (TBD)            |
| Finalize team name             | AREA-42        | Done        | 2026-06-09  | Final team name                  | Official team name: AREA-42                       |
| Finalize project idea          | AREA-42        | Done        | 2026-06-22  | Selected project idea            | Teacher approved direction on 2026-06-22 (internal preference 2026-06-21) |
| Restructure repository         | AREA-42        | In Progress | 2026-06-22  | Technical repo layout + docs     | GitHub Issue #11                                 |
| Validate candidate dataset     | All members    | In Progress | TBD         | Dataset quality notes            | PPE detection dataset (Roboflow, CC BY 4.0)      |

---

## 5. Current Priorities

1. Restructure the repository for technical work (GitHub Issue #11).
2. Validate the candidate PPE dataset (quality, classes, licensing).
3. Define the detailed technical plan for the MVP pipeline.
4. Assign DRIs to each planned component (`src/` modules).
5. Add the GitHub Project board link to the documentation.
6. Start MVP implementation (video input + PPE detection first).

---

## 6. Current Blockers

| Blocker                                 | Owner       | Status   | Needed Action                     |
| --------------------------------------- | ----------- | -------- | --------------------------------- |
| Dataset quality is not fully checked yet | All members | Open     | Validate candidate PPE dataset    |
| GitHub Project board link not added yet | AREA-42     | Open     | Add board link to docs (TBD)      |
| Component DRIs not assigned yet         | AREA-42     | Open     | Assign owners to `src/` modules   |

---

## 7. Role Draft

These roles are temporary and may change after the final project idea is selected.

| Member              | Temporary Role / Responsibility             | Notes         |
| ------------------- | ------------------------------------------- | ------------- |
| Roya Nasirova       | TBD                                         | To be updated |
| Adil Hasanov        | TBD                                         | To be updated |
| Elvin Nəsirov       | Coordination / Documentation / GitHub setup | Temporary     |
| Aysu Mammadova Anar | TBD                                         | To be updated |

---

## 8. Project Idea Tracking

This section tracked possible ideas before the final project was selected.

| Idea                                  | Suggested By | Possible Dataset            | Problem                              | Feasibility | Status   |
| ------------------------------------- | ------------ | --------------------------- | ------------------------------------ | ----------- | -------- |
| AI-Powered Workplace Safety Monitoring | AREA-42      | PPE detection (Roboflow)    | Detect missing PPE / safety risks    | Feasible    | Teacher-approved (2026-06-22) |

---

## 9. Dataset Research Tracking

| Dataset       | Source Link                                                  | Related Idea            | Size | Target Variable          | Quality Notes                | Status      |
| ------------- | ----------------------------------------------------------- | ----------------------- | ---- | ------------------------ | ---------------------------- | ----------- |
| PPE detection | https://universe.roboflow.com/testcasque/ppe-detection-qlq3d | Safety Monitoring (MVP) | TBD  | PPE classes (10 classes) | CC BY 4.0; validation ongoing | In Progress |

---

## 9a. Planned Technical Components

> All components below are **planned**, not implemented.

| Component             | Planned location     | Status  | DRI |
| --------------------- | -------------------- | ------- | --- |
| Video input           | `src/video/`         | Planned | TBD |
| PPE detection         | `src/detection/`     | Planned | TBD |
| Person tracking       | `src/tracking/`      | Planned | TBD |
| Violation rules       | `src/rules/`         | Planned | TBD |
| Persistent violation logic | `src/rules/`    | Planned | TBD |
| Incident capture      | `src/incidents/`     | Planned | TBD |
| Notifications         | `src/notifications/` | Planned | TBD |
| API                   | `src/api/`           | Planned | TBD |
| Monitoring UI         | `src/ui/`            | Planned | TBD |

---

## 10. Meeting Notes Summary

| Date       | Main Topic                   | Key Outcome                                                                                                | Next Step                            |
| ---------- | ---------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| 2026-06-08 | Initial coordination meeting | Teacher guidelines discussed, temporary roles created, daily meeting time selected, initial tasks assigned | Create GitHub repository and Plan.md |
| 2026-06-21 | Project idea discussion      | Team's internal preference: AI-Powered Workplace Safety Monitoring (not yet teacher-approved)              | Seek teacher approval; plan MVP      |
| 2026-06-22 | Teacher approval & restructure | Teacher approved the project direction; repo reorganized into technical layout; README/Plan/docs updated (Issue #11) | Validate dataset and assign DRIs     |

---

## 11. Update Rule

This file should be updated whenever:

* A task status changes
* A new task is assigned
* A blocker appears
* A blocker is solved
* A project idea is added
* A dataset is found
* A decision affects the roadmap
* A deadline changes

Small updates can be posted in Discord first, but important progress should eventually be reflected here.
