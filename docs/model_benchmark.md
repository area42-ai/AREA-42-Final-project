\# AREA-42: Model Benchmarking Report



This document establishes a repeatable benchmark framework for validating and comparing Vision Language Models (VLMs) tracking PPE violations (specifically hard hats) against ground-truth data.



\## 1. Benchmarking Methodology \& Evaluation Rules



To ensure strict, unbiased comparison, every model run must use the same raw evaluation videos and adhere to the following timing rules:



\### Timing \& Tolerance Rules

\* \*\*Initial Timestamp Tolerance:\*\* `±2 seconds` allowed for both start and end times compared to the ground-truth JSON.

\* \*\*Incident Alignment Criteria:\*\* A prediction is marked as \*\*Correct\*\* ONLY if:

&#x20; 1. The predicted incident count matches the expected count.

&#x20; 2. The violation type (`missing\_hard\_hat`) matches.

&#x20; 3. The status (`resolved` or `open`) matches at video end.

&#x20; 4. Both start and end timestamps fall within the `±2 seconds` tolerance window.

&#x20; 5. Visual validation confirms evidence frames support the claim.



\### Error Classification

Every failure must be logged into one of these strict categories:

\* `model\_error`: Model completely misses a violation or incorrectly triggers one (false positive/negative).

\* `transition\_error`: Flashing or unstable state transitions while a worker is putting on/taking off a helmet.

\* `api\_error`: HTTP 500, timeouts, rate limits, or file processing loops.

\* `pipeline\_error`: Issues with timestamp synchronization, video stripping, parsing failures, or frame aggregation.

\* `out\_of\_scope`: Multi-person overlaps, extreme low visibility, or unsupported angles.



\---



\## 2. Benchmark Baseline Matrix



\### System Architecture \& Configurations

\* \*\*Current Core Baseline Model:\*\* `gemma-4-26b-a4b-it` (Native Video Understanding via Google GenAI SDK). \*\*Processes the entire video natively as a single asset without manual frame breakdown.\*\*

\* \*\*Hosted Baseline Candidate:\*\* `meta/llama-3.2-90b-vision-instruct` (Hosted via pipeline). \*\*Requires discrete frame extraction (sampling) and sequential frame evaluation.\*\*

\* \*\*Video Preprocessing:\*\* Audio tracks are programmatically stripped via FFmpeg to optimize ingestion window before uploading.



\### Performance Summary Table



| Video | Model | Expected Incidents | Predicted Incidents | Start Error (s) | End Error (s) | Status Correct | Evidence Correct | False Positive | False Negative | Runtime (s) | API/Runtime Errors | Notes |

| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |

| \*\*sample\_video\_1\*\* | gemma-4-26b-a4b-it | 1 | 1 | 0.0 | 0.0 | Yes | Yes | 0 | 0 | \~14.5 | None | \*\*Native Video Mode:\*\* Understood the whole video context instantly. Flawless JSON extraction. |

| \*\*sample\_video\_1\*\* | llama-3.2-90b-vision | 1 | 1 | +1.5 | -1.0 | Yes | Yes | 0 | 0 | \~22.3 | None | \*\*Frame-Based Mode:\*\* Processes segmented frames. Required external timestamp matching and format normalization. |



\### Deployment Metrics



| Model | Hosted/Local | Runtime | Hardware | Sample Interval | Avg Frame Time | Total Video Time | JSON Stability |

| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |

| \*\*gemma-4-26b-a4b-it\*\* | Hosted (API) | GenAI Native Video | Google Cloud | \*\*N/A (Whole Video)\*\* | Native | 35.0s | \*\*High\*\* (Native structure validation built-in) |

| \*\*llama-3.2-90b-vision\*\*| Hosted | Custom Pipeline | Remote Node | 1 frame/sec | 85ms | 35.0s | \*\*Medium\*\* (Requires regex string sanitization) |



\---



\## 3. Findings \& Failures Analysis



\### Architectural Processing Breakdown

\* \*\*Gemma 4 Approach:\*\* Natively ingests the entire video context. Because it looks at the continuous video asset as a whole, it drastically minimizes `pipeline\_error` risks associated with frame-to-timestamp mapping.

\* \*\*Llama 3.2 Approach:\*\* Operates strictly on slice-by-slice extracted frames. This introduces external dependencies on frame-sampling intervals and can create edge-case inaccuracies during swift movements or `transition\_error` phases.



\### Identified Pipeline Issues

\* \*\*Asset Upload Inefficiencies:\*\* Passing the full video with audio increases execution latency. The automated FFmpeg sub-routine `remove\_audio\_with\_ffmpeg` successfully mitigates this by generating a transient `\_no\_audio` clip.

\* \*\*JSON Stability:\*\* Older pipelines struggle with raw text blocks wrapping markdown blocks (e.g. ` ```json `). The current Gemma implementation successfully intercepts this using a custom multi-layered `extract\_json()` regex function to isolate curly brackets `{ ... }`.



\---



\## 4. Operational Recommendations



1\. \*\*Primary Recommendation:\*\* Move forward with establishing \*\*Gemma 4 (26B)\*\* as the active core agent. Its native multi-modal handling of long-horizon temporal changes removes the overhead of manual frame sampling pipelines and provides better temporal cohesion.

2\. \*\*Fallback Strategy:\*\* Maintain `meta/llama-3.2-90b-vision-instruct` as the hosted fallback, keeping its discrete frame-extraction logic operational in case of API rate depletion.

3\. \*\*Action Items for Elvin:\*\* Fix tracking behaviors during `transition\_error` phases—specifically frames where a helmet is held mid-air before being fully worn, which is a known vulnerability for the frame-based Llama pipeline.

