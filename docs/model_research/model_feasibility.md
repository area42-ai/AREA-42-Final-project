# Model Evaluation Notes: Nemotron & Gemma 4 4B

This document summarizes our findings on **NVIDIA Nemotron** and **Google Gemma 4 (4B Quantized)** for integration into our safety monitoring pipeline.

---

## 1. NVIDIA Nemotron (Cloud VLM)

### Video Processing Speed

- **Inference Latency:** Raw visual analysis and reasoning take roughly **5 to 8 seconds** once the payload hits the cloud.
- **Network Consideration:** Because it ingests native video footage (`.mp4`), there is a brief upload pause. Base64 video strings are heavy, so a stable network connection is required to avoid timeout or size limit truncation.

### Live Video Ingestion Logic

To process a live CCTV feed continuously without hitting API limits, we use a **Sliding Window** approach:

1. **Local Buffering:** OpenCV captures frames locally in real-time.
2. **Chunking:** The feed is sliced into continuous **10-second segments** instead of infinite streaming.
3. **Asynchronous Shipping:** Every 10 seconds, the segment is exported as a temporary `.mp4` file and uploaded via a background thread, allowing the main script to immediately record the next chunk with zero data loss.

### Output Behavior & Parsing

- **The Issue:** Because Nemotron is a reasoning model, its natural output is structured in conversational "plain English" rather than structured JSON.
- **Current Status:** We have explicitly instructed it to keep outputs as short as possible. However, parsing loose text strings remains fragile.
- **Next Steps:** It still needs work. We will need to investigate custom parsers or explicit structured output flags to guarantee strict formatting without breaking the model's internal reasoning.

---

## 2. Google Gemma 4 (4B Quantized Local LLM)

### Local Performance

- **Speed & Feasibility:** When running locally on a laptop via Ollama, it is highly efficient and fast—**provided we turn off its 'thinking' (internal monologue) feature**.
- **Deployment:** This confirms we can easily run it completely locally on standard hardware without relying on paid or external cloud infrastructure.

### System Prompt & Formatting

- **Current Status:** Right now, it handles basic summaries quickly, but the raw output needs to match our project's exact formatting requirements.
- **Next Steps:** Once we finalize the exact layout we want for our final safety reports, we need to build and inject a proper **System Prompt** (or compile a custom Ollama Modelfile) to lock down the exact response structure and permanently disable the reasoning fluff.
