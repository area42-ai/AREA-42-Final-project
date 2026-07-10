"""AREA-42 Watch Out: Nemotron whole-video PPE pipeline (Pipeline A, step 1).

Sends the entire video to a hosted Nemotron model and returns a PLAIN-TEXT
temporal summary (never JSON). The text summary is the only input consumed by
the Gemma text-to-JSON converter (scripts/gemma_text_to_incident.py).

The model produces observations only; notification/alert decisions belong to a
separate deterministic rule engine.
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from dotenv import load_dotenv
import os

import sys
sys.stdout.reconfigure(encoding='utf-8')

REPO_ROOT = Path(__file__).resolve().parents[1]

if __package__:
    from .incident_contract import PPE_ITEMS, parse_ppe_items
else:  # direct-script execution
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from incident_contract import PPE_ITEMS, parse_ppe_items

load_dotenv(dotenv_path=REPO_ROOT / ".env")

DEFAULT_NEMOTRON_MODEL = os.getenv(
    "NVIDIA_NEMOTRON_MODEL",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
)
DEFAULT_OUTPUT_DIR = "outputs/nemotron_test"
SIZE_THRESHOLD_MB = 5.0

PPE_LABELS = {
    "hard_hat": "Hard hat / helmet worn on the head",
    "safety_vest": "High-visibility safety vest or reflective strips on the uniform",
    "safety_glasses": "Safety glasses / protective eyewear over the eyes",
    "gloves": "Protective gloves worn on the hands",
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
        help="Video filename inside data/test/ (e.g. video_05.mp4).",
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
        print(f"File size {size_mb:.2f} MB (within limits). Using original.")
        return video_path, False

    print(
        f"File size {size_mb:.2f} MB (exceeds {SIZE_THRESHOLD_MB} MB). "
        "Compressing to 4 FPS / 720p / no audio..."
    )
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix="_optimized.mp4")
    temp_output = Path(temp_file.name)
    temp_file.close()

    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(video_path),
                "-vf", "fps=4,scale=1280:720",
                "-an", "-vcodec", "libx264", "-crf", "28",
                str(temp_output),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        reduced_mb = temp_output.stat().st_size / (1024 * 1024)
        print(f"Compression complete. Payload reduced to {reduced_mb:.2f} MB.")
        return temp_output, True
    except Exception as encode_error:
        print(f"Compression failed ({encode_error}). Falling back to original.")
        return video_path, False


def main() -> None:
    args = parse_arguments()
    ppe_items = parse_ppe_items(args.ppe_items)

    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError(
            "NVIDIA_API_KEY was not found. Verify your local .env file."
        )

    video_path = REPO_ROOT / "data" / "test" / args.video_name
    if not video_path.exists():
        print(f"\n[ERROR]: Test video not found at: {video_path}")
        print("Place the file inside the 'data/test/' directory.")
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    processed_path, using_temp = maybe_compress_video(video_path)

    print("Encoding payload stream...")
    video_base64 = base64.b64encode(processed_path.read_bytes()).decode("utf-8")
    video_data_url = f"data:video/mp4;base64,{video_base64}"

    if using_temp and processed_path.exists():
        try:
            processed_path.unlink()
            print("Cleaned up temporary compressed asset.")
        except Exception as clean_error:
            print(f"Could not remove temporary file: {clean_error}")

    prompt = build_prompt(ppe_items)

    from openai import OpenAI

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
        timeout=300.0,
    )

    print("Analyzing timeline via NVIDIA gateway...")
    total_start = time.perf_counter()

    try:
        api_start = time.perf_counter()
        completion = client.chat.completions.create(
            model=DEFAULT_NEMOTRON_MODEL,
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
        api_latency = time.perf_counter() - api_start

        content = completion.choices[0].message.content
        reasoning = getattr(
            completion.choices[0].message, "reasoning_content", None
        )

        print("\n====================[ SAFETY LOG ]====================")
        if content and content.strip():
            print(content.strip())
        else:
            print("[Final text payload was empty.]")
            if reasoning and reasoning.strip():
                print("\n---[ Internal reasoning stream ]---")
                print(reasoning.strip())
        print("======================================================")

        total_time = time.perf_counter() - total_start
        print("\nPerformance:")
        print(f"   - API inference latency: {api_latency:.2f}s")
        print(f"   - Total pipeline time:   {total_time:.2f}s")

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
        print(f"Analysis saved to: {save_path}")

    except Exception as error:
        print(f"\n[PIPELINE FAILURE]: {error}")
        raise


if __name__ == "__main__":
    main()
