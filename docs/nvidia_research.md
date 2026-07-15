# AREA-42: Research Summary & MVP Architecture Report

**Project:** AI Workplace Safety PPE Detection

**Blueprint Reference:** NVIDIA Video Search and Summarization (VSS)

---

## 1. Executive Summary & Architecture Overview

This document outlines how the **AREA-42** team will adapt NVIDIA’s Video Search and Summarization (VSS) blueprint into a lean, cost-effective, production-ready workplace safety monitoring system.

Instead of hosting a massive, enterprise-grade data center infrastructure locally (which requires costly A100/H100 GPUs and a complex Kubernetes/Triton stack), our architecture leverages **NVIDIA’s Cloud Hosted APIs** via the NVIDIA API Catalog (`build.nvidia.com`). This fulfills the professor's explicit directive to use hosted endpoints while adding a highly specialized construction-safety dimension.

---

## 2. Answers to Research Questions

### How does NVIDIA ingest live and recorded video?

- **NVIDIA VSS Approach:** Uses **NVIDIA DeepStream** to ingest live camera feeds and decode high-throughput video streams in an industrial environment.
- **Our Adaptation:** We substitute DeepStream with a lightweight Python/OpenCV video ingestion engine. The script processes local camera streams or recorded footage and uses a frame-sampling mechanism to downsample the feed to **4 Frames Per Second (FPS)** to meet the specific technical guidelines of the cloud reasoner model.

### How are detections converted into candidate alerts?

- **NVIDIA VSS Approach:** Employs real-time vision trackers and multi-modal models to turn visual frames into continuous textual captions.
- **Our Adaptation:** We prompt the Vision-Language Model (**Cosmos 3 Nano Reasoner**) to act as our safety auditor. It performs visual chain-of-thought reasoning directly on the 4 FPS video clips to extract explicit safety violations (e.g., missing hard hats or vests).

### How are alerts verified to reduce false positives?

- **NVIDIA VSS Approach:** Passes continuous textual logs to a secondary downstream LLM or an automated validation layer to cross-reference rules and eliminate edge-case errors.
- **Our Adaptation:** We use **Structured Outputs** (via Pydantic or strict JSON schema enforcement) inside the API payload. This forces the model to fill out an explicit template rather than generating free-form text. For advanced validation, a lightweight text LLM like **Nemotron-Nano-9b-v2** can filter incoming alerts against OSHA compliance rules to filter out repetitive or false notifications.

### How are incident frames or clips stored and shown to an operator?

- **NVIDIA VSS Approach:** Indexes text captions into a vector database via Retrieval-Augmented Generation (RAG) for natural language querying by an operator.
- **Our Adaptation:** We skip the heavy RAG/Vector database infrastructure. Instead, we use a file-based **SQLite database** (or local JSON log) to maintain state and record violations. A web dashboard built using **Streamlit** or **Gradio** displays the active camera feed alongside an interactive, real-time alert table for the site supervisor.

---

## 3. Simplified Pipeline Diagram

```
[ Live CCTV / Video Feed ]
           │
           ▼
┌──────────────────────────────────────┐
│  Local Ingestion Engine (OpenCV)     │
│  - Captures frames from source       │
│  - Downsamples to 4 FPS payload      │
└──────────────────────────────────────┘
           │
           ▼ (Base64 .mp4 Upload / HTTPS)
┌──────────────────────────────────────┐
│  NVIDIA API Catalog (Cloud Servers)  │
│  - nvidia/cosmos3-nano-reasoner      │
│  - Optional: nemotron-nano-9b-v2     │
└──────────────────────────────────────┘
           │
           ▼ (Enforced JSON Response)
┌──────────────────────────────────────┐
│  State Management & UI Backend       │
│  - Filters repeating alerts          │
│  - Logs incidents into SQLite        │
└──────────────────────────────────────┘
           │
           ▼
[ Streamlit/Gradio Supervisor Dashboard ]

```

---

## 4. Component Evaluation (Adopt / Adapt / Reject)

| NVIDIA VSS Component                | Status     | Strategy & Implementation                                                                                                                        |
| ----------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **NVIDIA Cosmos VLM**               | **Adopt**  | Used directly via cloud hosted endpoints (`nvidia/cosmos3-nano-reasoner`). Conducts core visual safety analysis.                                 |
| **NVIDIA Nemotron LLM**             | **Adapt**  | Optional downstream component (`nvidia-nemotron-nano-9b-v2`) used purely via Cloud API for text report formatting and secondary validation.      |
| **NVIDIA DeepStream**               | **Reject** | Replaced with standard **OpenCV** to drastically simplify local video capture and preprocessing dependencies.                                    |
| **Local Triton / Docker Container** | **Reject** | Bypassed completely because we run on the **Hosted API Endpoints** instead of self-hosting local weights (avoiding the Linux/Docker constraint). |
| **RAG / Vector Database**           | **Reject** | Replaced with a lightweight relational **SQLite** database for event logging to fit student MVP scope.                                           |

---

## 5. Technical Risks, Constraints, and Dependencies

- **API Key Rate Limits:** The free developer tier provides a ceiling of **40 Requests Per Minute (RPM)**.
- _Mitigation:_ Local frame-sampling logic will guarantee that files are only batched and pushed every 2–3 seconds or when motion thresholds are met, keeping us well below the limit.

- **Input Specifications:** The Cosmos Reasoner requires input videos to be in `.mp4` format and explicitly requests a **4 FPS configuration**.
- _Mitigation:_ The Python backend will gather individual frames via OpenCV, bundle them in memory, and export them precisely according to the 4 FPS standard before hitting the API.

- **Network Latency:** Because inference happens in the cloud rather than locally on the edge, alert delivery is subject to network speeds.
- _Mitigation:_ Ideal for macro-level site monitoring and automated shift reporting rather than millisecond-level instant machinery shutdowns.

---

## 6. Recommended MVP Stack

- **Programming Language:** Python 3.10+
- **Video Handling:** OpenCV (`opencv-python`)
- **Core Vision Brain:** `nvidia/cosmos3-nano-reasoner` (Free Hosted API Endpoint via OpenAI-compatible SDK)
- **Data Formatting Layer:** Pydantic / JSON schema constraints
- **Database & State Management:** SQLite (Built-in to Python)
- **Frontend Web Dashboard:** Streamlit (Pure Python UI generation)
- **Project Financial Cost:** **$0.00** (Utilizes NVIDIA's free development sandbox endpoints; zero local enterprise GPU requirements).
