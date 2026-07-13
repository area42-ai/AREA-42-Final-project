"""Experimental direct-video Gemma baseline (source_pipeline: gemma_direct).

The required primary architecture uses Nemotron text followed by Gemma
text-to-JSON conversion (scripts/gemma_text_to_incident.py). This script sends
the whole video directly to Gemma 4 and is kept only as an experimental
direct-video baseline. It emits the SAME shared normalized contract as the other
pipelines (scripts/incident_contract.py). Gemma makes no notification decisions.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

if __package__:
    from .incident_contract import (
        PPE_ITEMS,
        build_envelope,
        default_quality,
        normalized_incidents_from_model,
        parse_ppe_items,
    )
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from incident_contract import (
        PPE_ITEMS,
        build_envelope,
        default_quality,
        normalized_incidents_from_model,
        parse_ppe_items,
    )

load_dotenv()

MODEL = os.getenv("GOOGLE_GEMMA_MODEL", "gemma-4-26b-a4b-it")
DEFAULT_PROCESSING_TIMEOUT_SECONDS = 600


def build_prompt(ppe_items: list[str]) -> str:
    scope = ", ".join(ppe_items)
    return f"""
[SYSTEM DIRECTIVE: You are an automated PPE video observer. Output ONLY one raw
JSON object. No markdown fences, no reasoning text.]

Watch the entire video and analyze these PPE items only: {scope}.

Produce one incident per PPE item per confirmed period during which that item
is MISSING (the relevant body area is visible and the item is not worn).

Rules:
- Allowed status values: present, missing, unknown, not_applicable.
- If the relevant body area is not visible, the item is unknown - NOT missing.
- Not being able to see an item is never a violation.
- Do not invent items, people, or actions.
- Times are numeric seconds (floats).
- If the item is put back on, set end_seconds to that time; otherwise null.
- Do not decide notifications.

Return exactly this JSON structure and nothing else:
{{
  "summary": "short factual summary of the timeline",
  "incidents": [
    {{
      "ppe_item": "hard_hat",
      "status": "missing",
      "start_seconds": 2.0,
      "end_seconds": 5.0,
      "minimum_confirmed_duration_seconds": null,
      "confidence": 0.9,
      "action_sequence": [
        {{
          "event": "ppe_removed",
          "ppe_item": "hard_hat",
          "timestamp_seconds": 2.0,
          "description": "Worker removes the hard hat."
        }}
      ]
    }}
  ]
}}
""".strip()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Experimental direct-video baseline: native video understanding "
            "with Gemma 4. Not the production Nemotron->Gemma Pipeline A."
        )
    )
    parser.add_argument("--video", required=True, help="Path to MP4 video.")
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Path for the normalized Incident JSON. "
            "Default: <output-dir>/<video_stem>_normalized_incident.json."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Directory for diagnostic/raw artifacts. Default: results.",
    )
    parser.add_argument(
        "--ppe-items",
        default=None,
        help=f"Comma-separated PPE scope. Default: {','.join(PPE_ITEMS)}.",
    )
    parser.add_argument(
        "--processing-timeout-seconds",
        type=float,
        default=DEFAULT_PROCESSING_TIMEOUT_SECONDS,
        help="Max seconds to wait for remote video processing. Default: 600.",
    )
    return parser.parse_args()


def extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("The model response does not contain a JSON object.")
    parsed = json.loads(cleaned[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("The model response JSON is not an object.")
    return parsed


def assemble_document(
    parsed_result: dict[str, Any],
    video_id: str,
    model: str,
    ppe_items: list[str],
) -> dict[str, Any]:
    """Deterministically build the normalized gemma_direct document."""
    incidents, warnings = normalized_incidents_from_model(
        parsed_result.get("incidents", []),
        ppe_items,
    )
    summary = parsed_result.get("summary", "")
    if not isinstance(summary, str):
        summary = ""
        warnings.append("summary was not a string; reset to ''.")

    return build_envelope(
        video_id=video_id,
        source_pipeline="gemma_direct",
        models=[model],
        analysis_scope=ppe_items,
        incidents=incidents,
        summary=summary,
        quality=default_quality(parse_success=True, warnings=warnings),
    )


def wait_until_ready(client, file_obj, timeout_seconds):
    print("Waiting for video processing...")
    start_time = time.monotonic()
    while True:
        current = client.files.get(name=file_obj.name)
        state = getattr(current, "state", None)
        if state:
            state_name = str(state).upper()
            print(f"Current state: {state_name}")
            if "ACTIVE" in state_name:
                return current
            if "FAILED" in state_name:
                raise RuntimeError("Video processing failed.")
        if time.monotonic() - start_time >= timeout_seconds:
            raise TimeoutError(
                f"Timed out after {timeout_seconds:.0f} seconds waiting for "
                "the remote video to become ACTIVE."
            )
        time.sleep(5)


def remove_audio_with_ffmpeg(input_path: Path) -> Path:
    """Strip the audio track using FFmpeg, falling back to the original."""
    try:
        import imageio_ffmpeg

        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        print(f"FFmpeg found at: {ffmpeg_path}")
    except Exception:
        ffmpeg_path = "ffmpeg"

    temp_dir = Path(tempfile.gettempdir())
    output_path = temp_dir / f"{input_path.stem}_no_audio{input_path.suffix}"
    cmd = [
        ffmpeg_path, "-i", str(input_path), "-c", "copy", "-an", "-y",
        str(output_path),
    ]
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            print("FFmpeg failed. Using original video.")
            return input_path
        print(f"Audio removed successfully: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error running FFmpeg: {e}")
        print("Using original video.")
        return input_path


def delete_remote_file(client, uploaded_file) -> None:
    """Delete the uploaded remote file only if one was actually created."""
    if uploaded_file is None:
        return
    try:
        print("Deleting uploaded video...")
        client.files.delete(name=uploaded_file.name)
        print("Uploaded file deleted.")
    except Exception as e:
        print(f"Delete warning: {e}")


def save_diagnostic(
    output_dir: Path,
    stem: str,
    model: str,
    video: str,
    model_text: str,
    parse_success: bool,
    parse_error: str | None,
    parsed_result: dict[str, Any],
) -> Path:
    diagnostic = {
        "model": model,
        "video": video,
        "model_text": model_text,
        "parse_success": parse_success,
        "parse_error": parse_error,
        "parsed_result": parsed_result,
    }
    diagnostic_path = output_dir / f"{stem}_diagnostic.json"
    diagnostic_path.write_text(
        json.dumps(diagnostic, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return diagnostic_path


def main() -> None:
    args = parse_arguments()
    ppe_items = parse_ppe_items(args.ppe_items)

    video_path = Path(args.video)
    if not video_path.exists():
        raise FileNotFoundError(video_path)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = (
        Path(args.output)
        if args.output
        else output_dir / f"{video_path.stem}_normalized_incident.json"
    )

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY environment variable not found.")

    from google import genai

    client = genai.Client(api_key=api_key)
    temp_video_path = remove_audio_with_ffmpeg(video_path)
    use_temp = temp_video_path != video_path
    uploaded_file = None

    try:
        print("Uploading video...")
        uploaded_file = client.files.upload(file=str(temp_video_path))
        uploaded_file = wait_until_ready(
            client, uploaded_file, args.processing_timeout_seconds
        )

        print("Starting video analysis...")
        response = client.models.generate_content(
            model=MODEL,
            contents=[uploaded_file, build_prompt(ppe_items)],
        )
        model_text = response.text or ""

        parse_success = True
        parse_error: str | None = None
        parsed_result: dict[str, Any] = {}
        try:
            parsed_result = extract_json(model_text)
        except ValueError as error:
            parse_success = False
            parse_error = str(error)

        diagnostic_path = save_diagnostic(
            output_dir=output_dir,
            stem=video_path.stem,
            model=MODEL,
            video=str(video_path),
            model_text=model_text,
            parse_success=parse_success,
            parse_error=parse_error,
            parsed_result=parsed_result,
        )
        print(f"Diagnostic saved: {diagnostic_path}")

        if not parse_success:
            print(
                "\n[PARSE FAILURE] The model response could not be parsed as "
                f"JSON: {parse_error}"
            )
            sys.exit(1)

        document = assemble_document(
            parsed_result, video_path.stem, MODEL, ppe_items
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(document, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print("\nAnalysis completed.")
        print(f"Normalized incident: {output_path}")
        print(f"Incident detected: {document['incident_detected']}")
        print(f"Incident count: {len(document['incidents'])}")
        print(f"Summary: {document['summary']}")

    except SystemExit:
        raise
    except Exception as e:
        import traceback

        print(traceback.format_exc())
        print(type(e))
        print(e)
        if hasattr(e, "response"):
            print(e.response)
            try:
                print(e.response.text)
            except Exception:
                pass
        raise

    finally:
        if use_temp and temp_video_path.exists():
            try:
                print(f"\nDeleting temporary file: {temp_video_path}")
                temp_video_path.unlink()
                print("Temporary file deleted.")
            except Exception as e:
                print(f"Delete warning: {e}")
        delete_remote_file(client, uploaded_file)


if __name__ == "__main__":
    main()
