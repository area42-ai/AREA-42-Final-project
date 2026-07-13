# Project Context — Watch Out

Shared project context for all team members and AI assistants. This document
captures the current understanding of the product. Where information is not yet
confirmed, it is marked clearly. Do not treat **Proposed** or **TBD** items as
facts.

## Team

- **AREA-42**.

## Product

- **Official product name:** **Watch Out**.
- An AI-powered workplace safety monitoring system that analyzes video to detect
personal protective equipment (PPE) / safety violations and surface them as
timestamped evidence with notifications.

## Project status

- Technical planning. Implementation of the pipeline has not started; the `src/`
modules are planned placeholders.
- Current technical direction: **API-first** (see `docs/ARCHITECTURE.md`).



## Problem statement

Workplaces such as construction sites, warehouses, and factories require workers
to wear PPE (helmets, vests, gloves, goggles, boots). Manual monitoring through
CCTV is slow, inconsistent, and hard to scale, so safety violations are often
noticed too late — only after an incident has already happened.

## Intended user

- Safety officers / supervisors responsible for monitoring PPE compliance on a
site, who need violations surfaced quickly with evidence rather than after the
fact.



## Current MVP boundary

The MVP aims to demonstrate the end-to-end pipeline on a **single video source**:

- ingest a video file (or a single camera stream);
- send sampled frames to an **external NVIDIA model via API** for inference;
- interpret the response into safety events / violations;
- apply persistent-violation logic so a violation must last a sustained period
before it counts (to reduce false alarms);
- capture timestamped evidence (frame/clip) for a confirmed violation;
- send a basic notification and/or present results in a simple dashboard.

---



## Confirmed

These are confirmed current decisions.

- The team is **AREA-42**.
- The official product name is **Watch Out**.
- The current technical direction is **API-first**.
- The project will use an **external NVIDIA model through an API key** as the
primary MVP approach, rather than training a custom model.
- A **full training dataset is not a required dependency** for the current MVP.
- A **small evaluation set is still required** to sanity-check behavior even when
using an external API model.
- GitHub is the source of truth for code, tasks, decisions, and documentation.
- All changes go through **task branches and Pull Requests**; no direct work on
`main`.
- Raw datasets, videos, model weights, sensitive API responses, generated clips,
secrets, virtual environments, and experiment outputs must **not** be committed
(see `docs/ASSET_POLICY.md`).
- Representative test videos will be stored **outside Git** (most likely Google
Drive).
- The team uses **Gemini** for task discussion/planning and **Antigravity /
Cursor** for repository-aware implementation (see `docs/AI_WORKFLOW.md`).



## Proposed

These reflect the current proposed direction but are not finalized.

- The end-to-end pipeline described in `docs/ARCHITECTURE.md`
(frame sampling → preprocessing → NVIDIA model API → response normalization →
event interpretation → evidence → notification/dashboard).
- The planned module layout under `src/` (`video/`, `detection/`, `tracking/`,
`rules/`, `incidents/`, `notifications/`, `api/`, `ui/`).
- Proposed local asset locations: `data/raw/`, `data/test/`, `assets/demo/`,
`outputs/`, `models/weights/` (see `docs/ASSET_POLICY.md`).



## Assumptions

- An NVIDIA-hosted model exists that can perform the required visual inference
via API, accessible with an API key. The specific model is not yet selected.
- Frame sampling (rather than every frame) will be sufficient for the MVP.
- A small, manually collected evaluation set will be enough to validate behavior
for a demo.



## TBD

Genuinely unknown — do not invent these.

- Exact NVIDIA model name, API endpoint, capabilities, pricing, and rate/usage
limits.
- The supported event/violation classes the chosen model can detect.
- Accuracy, latency, and other performance metrics.
- Frame sampling rate and persistent-violation thresholds (N seconds).
- Final notification channel(s) and dashboard scope.
- Whether the previously identified candidate PPE dataset (Roboflow,
CC BY 4.0; see `data/README.md`) is used as the small evaluation set.
- Component DRIs (owners) for each planned `src/` module.
- GitHub Project board link.

---



## Current product flow

1. A video file or single camera stream is provided as input.
2. Frames are sampled/extracted and preprocessed.
3. Sampled frames are sent to the external NVIDIA model via API.
4. The API response is normalized into a consistent internal format.
5. The system interprets detections into safety events / violations.
6. Persistent-violation logic confirms a violation only after it is sustained.
7. Timestamped evidence (frame/clip) is captured for confirmed violations.
8. A notification is sent and/or results are shown in a simple dashboard.



## Out of scope for the first MVP

- Training or fine-tuning a custom model as the primary approach.
- A full/large training dataset as a required dependency.
- Multi-camera scaling, load balancing, and high availability.
- Advanced analytics, dashboards, and reporting.
- User accounts, roles, and permissions.
- Production-grade deployment.

