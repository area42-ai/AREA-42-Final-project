# Architecture — Watch Out (Proposed, API-first)

This document describes the **current proposed** API-first architecture for
**Watch Out**. It is a design reference, not implemented code. No application
code is created by this document. Treat everything here as **Proposed** unless it
is listed under "Confirmed design" below.

> Accuracy note: the external model is an NVIDIA model accessed via API. The
> exact model, endpoint, capabilities, pricing, and limits are **TBD** (see
> `docs/PROJECT_CONTEXT.md`). Do not invent them.

## Pipeline overview

```text
Video file or camera stream
  → frame sampling / extraction
  → preprocessing
  → NVIDIA model API request
  → normalized inference response
  → event / violation interpretation
  → timestamped evidence
  → saved evidence clip or frame
  → notification or dashboard presentation
```

## Components

| Stage | Responsibility | Inputs | Outputs | Planned location |
| ----- | -------------- | ------ | ------- | ---------------- |
| Video input | Read a video file or single camera stream | File path / stream URL | Decoded frames + timestamps | `src/video/` |
| Frame sampling / extraction | Select frames (e.g. every Nth frame) to limit API calls | Decoded frames | Sampled frames + timestamps | `src/video/` |
| Preprocessing | Prepare frames for the API (resize/encode as required) | Sampled frames | API-ready frame payloads | `src/detection/` |
| NVIDIA model API request | Call the external NVIDIA model with the frame payload | Frame payload + API key | Raw inference response | `src/detection/` |
| Response normalization | Convert the raw API response into a consistent internal format | Raw API response | Normalized detections | `src/detection/` |
| Event / violation interpretation | Map detections to safety events; apply persistent-violation logic | Normalized detections + per-person context | Confirmed violations | `src/rules/`, `src/tracking/` |
| Timestamped evidence | Attach timestamps and context to a confirmed violation | Confirmed violation | Evidence metadata | `src/incidents/` |
| Saved evidence clip / frame | Persist a frame or clip for the violation | Frame/clip + metadata | Evidence file (stored outside Git) | `src/incidents/` |
| Notification / dashboard | Notify responsible people and/or present results | Evidence + metadata | Notification / UI view | `src/notifications/`, `src/api/`, `src/ui/` |

> Person tracking (`src/tracking/`) is **proposed** to make violations
> per-person rather than per-frame. Whether and how tracking is done may depend
> on the chosen model's capabilities (TBD).

## Expected inputs and outputs (system level)

- **Input:** a single video file or one camera stream.
- **Output:** confirmed, timestamped violations with saved evidence (frame or
  clip stored outside Git) plus a notification and/or dashboard entry.

## External dependency boundary

- The only external inference dependency is the **NVIDIA model API**.
- The boundary is the request/response between preprocessing and response
  normalization. Everything inside the boundary (normalization, interpretation,
  evidence, presentation) is owned by Watch Out.
- The API key is configuration/secret and must never be committed (see
  `docs/ASSET_POLICY.md`).
- The specific model, endpoint, request/response schema, capabilities, pricing,
  and limits are **TBD**; normalization isolates the rest of the system from
  these details.

## Failure handling considerations (proposed)

- Treat the API as unreliable: handle network errors, non-200 responses,
  malformed/empty responses, and partial results.
- Use retries with backoff for transient failures; fail gracefully and skip a
  frame rather than crashing the pipeline.
- Log failures without storing sensitive payloads; degrade to "no detection for
  this frame" instead of producing false violations.

## API timeout / rate-limit considerations (proposed)

- Apply per-request timeouts so a slow API call does not stall the pipeline.
- Frame sampling reduces call volume; sampling rate is **TBD**.
- Respect the provider's rate limits (limits **TBD**); throttle or queue
  requests as needed and back off on rate-limit responses.

## Privacy and security considerations (proposed)

- Video may contain people; treat frames and evidence as sensitive.
- Keep API keys in environment variables / secrets, never in code or Git.
- Do not commit videos, frames, clips, or raw API responses (see
  `docs/ASSET_POLICY.md`).
- Store evidence and test/demo media outside Git in approved external storage.
- Avoid logging raw frames or sensitive API response content.

## Confirmed vs proposed design

- **Confirmed design:**
  - The architecture is API-first.
  - Inference is performed by an external NVIDIA model accessed via an API key,
    not a custom-trained model (for the MVP).
  - Datasets, videos, weights, secrets, and generated outputs are not committed.

- **Proposed design (subject to change):**
  - The specific stage breakdown, module boundaries, sampling strategy,
    tracking approach, persistent-violation thresholds, evidence format, and
    notification/dashboard scope.
  - All concrete model/API details, which remain **TBD**.
