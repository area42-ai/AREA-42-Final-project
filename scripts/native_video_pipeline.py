"""AREA-42 Watch Out: Nemotron whole-video PPE pipeline (Pipeline A, step 1).

Sends the entire video to a hosted Nemotron model and returns a PLAIN-TEXT
temporal summary (never JSON). The text summary is the only input consumed by
the Gemma text-to-JSON converter (scripts/gemma_text_to_incident.py).

The model produces observations only; notification/alert decisions belong to a
separate deterministic rule engine.

Accepts either:
  - a positional video_name resolved inside data/test/ (original batch flow), or
  - an explicit --video-path pointing anywhere on disk (used by the
    event-driven live pipeline, whose segments live under data/event_segments/).

Upload payloads are compressed aggressively (540p / 3 FPS / CRF~30) before
being sent to Nemotron -- more than enough fidelity for PPE presence/absence
detection -- to keep hosted inference latency and timeout risk down. Transient
network/server errors are retried a bounded number of times with exponential
backoff; a request that still fails (including a timeout) is logged and
propagated so the caller (run_pipeline_a.py / segment_dispatcher.py) can move
the segment to failed_segments and continue processing future events.
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from dotenv import load_dotenv
import os

sys.stdout.reconfigure(encoding='utf-8')

REPO_ROOT = Path(__file__).resolve().parents[1]

if __package__:
    from .incident_contract import PPE_ITEMS, parse_ppe_items
else:  # direct-script execution
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from incident_contract import PPE_ITEMS, parse_ppe_items

load_dotenv(dotenv_path=REPO_ROOT / ".env")

logger = logging.getLogger(__name__)

_nemotron_env = os.getenv("NVIDIA_NEMOTRON_MODEL", "").strip()
DEFAULT_NEMOTRON_MODEL = (
    _nemotron_env if _nemotron_env else "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
)
DEFAULT_OUTPUT_DIR = "outputs/nemotron_test"
SIZE_THRESHOLD_MB = 5.0

# Request-level configuration. The original fixed 300s timeout with no
# retry meant a single slow/transient failure discarded an entire event.
NEMOTRON_TIMEOUT_SECONDS = float(os.getenv("NEMOTRON_TIMEOUT_SECONDS", "120"))
NEMOTRON_MAX_RETRIES = int(os.getenv("NEMOTRON_MAX_RETRIES", "2"))
NEMOTRON_RETRY_BASE_DELAY_SECONDS = float(
    os.getenv("NEMOTRON_RETRY_BASE_DELAY_SECONDS", "2")
)

# Aggressive compression suitable for PPE detection: full color/detail on a
# worker's body is not needed at broadcast resolution/framerate for a
# present/absent/unknown judgement.
COMPRESSION_FPS = 3
COMPRESSION_HEIGHT = 540
COMPRESSION_CRF = 30

PPE_LABELS = {
    "hard_hat": "Hard hat / helmet worn on the head",
    "safety_vest": "High-visibility safety vest or reflective strips on the uniform",
    "safety_glasses": "Safety glasses / protective eyewear over the eyes",
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan a whole video for PPE compliance using a hosted Nemotron "
            "model and save a plain-text temporal summary."
        )
    )
    parser.add_argument(
        "video_name",
        type=str,
        nargs="?",
        default=None,
        help="Video filename inside data/test/ (e.g. video_05.mp4).",
    )
    parser.add_argument(
        "--video-path",
        default=None,
        help=(
            "Full/relative path to a video anywhere on disk (e.g. an "
            "event-driven segment produced by the live pipeline)."
        ),
    )
    parser.add_argument(
        "--ppe-items",
        default=None,
        help=(
            "Comma-separated PPE items to check. "
            f"Default: {','.join(PPE_ITEMS)}."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for the summary JSON. Default: {DEFAULT_OUTPUT_DIR}.",
    )
    return parser.parse_args()


def build_prompt(ppe_items: list[str]) -> str:
    bullet_lines = "\n".join(
        f"{position}. {PPE_LABELS[item]}"
        for position, item in enumerate(ppe_items, start=1)
    )
    return f"""
[SYSTEM DIRECTIVE: You are an automated safety-compliance observer. You watch a
surveillance video and output a high-accuracy PLAIN-TEXT temporal summary based
strictly on what is visible. You do not make notification or alert decisions.]

Task: Analyze the entire video timeline. Identify every distinct worker who
appears on screen (there is often more than one). For EACH worker separately,
give a short identifying description (e.g. clothing color, role) and their
approximate on-screen time range, then assess each of the following PPE items
for that worker:
{bullet_lines}

For every PPE item, describe across the timeline when it is:
- clearly present (worn correctly);
- clearly absent (not worn while the relevant body area is visible);
- impossible to evaluate (the relevant body area is not visible).

Reporting rules:
- Give approximate start and end timestamps for each confirmed period of
  absence of each item, for each worker.
- Describe every status change for each item for each worker (e.g. helmet
  removed, vest put on).
- If a body area is not visible, say it is not possible to evaluate. Not being
  able to see an item is NOT a violation.
- Do not invent objects, people, or actions that are not visible.
- Do not decide whether to send any notification or alert.

Strict formatting constraints:
- Do NOT wrap the response in JSON.
- Do NOT use markdown code fences.
- Do NOT include bounding boxes, coordinates, or positional markers.
- Output only the final plain-text temporal summary.
""".strip()


def maybe_compress_video(video_path: Path) -> tuple[Path, bool]:
    size_mb = video_path.stat().st_size / (1024 * 1024)
    if size_mb <= SIZE_THRESHOLD_MB:
        logger.info("File size %.2f MB (within limits). Using original.", size_mb)
        return video_path, False

    logger.info(
        "File size %.2f MB (exceeds %.1f MB). Compressing to %dp / %dfps / "
        "CRF%d for Nemotron upload...",
        size_mb,
        SIZE_THRESHOLD_MB,
        COMPRESSION_HEIGHT,
        COMPRESSION_FPS,
        COMPRESSION_CRF,
    )
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix="_optimized.mp4")
    temp_output = Path(temp_file.name)
    temp_file.close()

    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(video_path),
                "-vf", f"fps={COMPRESSION_FPS},scale=-2:{COMPRESSION_HEIGHT}",
                "-an", "-vcodec", "libx264", "-crf", str(COMPRESSION_CRF),
                str(temp_output),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        reduced_mb = temp_output.stat().st_size / (1024 * 1024)
        logger.info("Compression complete. Payload reduced to %.2f MB.", reduced_mb)
        return temp_output, True
    except Exception as encode_error:
        logger.warning(
            "Compression failed (%s). Falling back to original.", encode_error
        )
        return video_path, False


def call_nemotron_with_retries(
    client,
    model: str,
    prompt: str,
    video_data_url: str,
    max_retries: int = NEMOTRON_MAX_RETRIES,
    base_delay_seconds: float = NEMOTRON_RETRY_BASE_DELAY_SECONDS,
):
    """Call Nemotron, retrying only on transient network/server errors.

    Non-transient errors (bad request, auth, etc.) are raised immediately
    without retrying, since retrying them cannot succeed.
    """
    from openai import (
        APIConnectionError,
        APITimeoutError,
        InternalServerError,
        RateLimitError,
    )

    transient_errors = (
        APITimeoutError,
        APIConnectionError,
        RateLimitError,
        InternalServerError,
    )

    attempt = 0
    delay = base_delay_seconds
    while True:
        try:
            return client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "video_url", "video_url": {"url": video_data_url}},
                        ],
                    }
                ],
                temperature=0.4,
                max_tokens=4096,
                stream=False,
            )
        except transient_errors as error:
            if attempt >= max_retries:
                logger.error(
                    "Nemotron request failed after %d attempt(s): %s",
                    attempt + 1,
                    error,
                )
                raise
            logger.warning(
                "Transient Nemotron error (attempt %d/%d): %s -- retrying in %.1fs",
                attempt + 1,
                max_retries + 1,
                error,
                delay,
            )
            time.sleep(delay)
            delay *= 2
            attempt += 1


def main() -> None:
    args = parse_arguments()
    ppe_items = parse_ppe_items(args.ppe_items)

    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError(
            "NVIDIA_API_KEY was not found. Verify your local .env file."
        )

    if args.video_path:
        video_path = Path(args.video_path)
        if not video_path.is_absolute():
            video_path = (REPO_ROOT / video_path).resolve()
        if not video_path.exists():
            logger.error("Video not found at --video-path: %s", video_path)
            sys.exit(1)
    else:
        if not args.video_name:
            logger.error("Provide either video_name or --video-path.")
            sys.exit(1)
        video_path = REPO_ROOT / "data" / "test" / args.video_name
        if not video_path.exists():
            logger.error("Test video not found at: %s", video_path)
            logger.error("Place the file inside the 'data/test/' directory.")
            sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    processed_path, using_temp = maybe_compress_video(video_path)

    logger.info("Encoding payload stream...")
    video_base64 = base64.b64encode(processed_path.read_bytes()).decode("utf-8")
    video_data_url = f"data:video/mp4;base64,{video_base64}"

    if using_temp and processed_path.exists():
        try:
            processed_path.unlink()
            logger.info("Cleaned up temporary compressed asset.")
        except Exception as clean_error:
            logger.warning("Could not remove temporary file: %s", clean_error)

    prompt = build_prompt(ppe_items)

    from openai import OpenAI

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
        timeout=NEMOTRON_TIMEOUT_SECONDS,
    )

    logger.info("Analyzing timeline via NVIDIA gateway...")
    total_start = time.perf_counter()

    try:
        api_start = time.perf_counter()
        completion = call_nemotron_with_retries(client, DEFAULT_NEMOTRON_MODEL, prompt, video_data_url)
        api_latency = time.perf_counter() - api_start

        content = completion.choices[0].message.content
        reasoning = getattr(
            completion.choices[0].message, "reasoning_content", None
        )

        if content and content.strip():
            logger.info("Nemotron summary received (%d chars).", len(content.strip()))
        else:
            logger.warning("Final text payload was empty.")
            if reasoning and reasoning.strip():
                logger.debug("Internal reasoning stream: %s", reasoning.strip())

        total_time = time.perf_counter() - total_start
        logger.info(
            "Performance: API inference latency=%.2fs, total pipeline time=%.2fs",
            api_latency,
            total_time,
        )

        output_payload = {
            "source_file": str(video_path),
            "model": DEFAULT_NEMOTRON_MODEL,
            "video": str(video_path),
            "analysis_scope": ppe_items,
            "metrics": {
                "api_inference_latency_seconds": round(api_latency, 2),
                "total_execution_time_seconds": round(total_time, 2),
            },
            "internal_thinking": reasoning,
            "summary_output": content.strip() if content else None,
        }

        save_path = output_dir / f"nemotron_{video_path.stem}_summary.json"
        save_path.write_text(
            json.dumps(output_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Analysis saved to: %s", save_path)

    except Exception as error:
        # Includes exhausted-retry timeouts. Propagating (non-zero exit) is
        # what allows run_pipeline_a.py / segment_dispatcher.py to move this
        # segment to failed_segments and continue with future events.
        logger.error("Pipeline failure: %s", error)
        raise


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    main()
