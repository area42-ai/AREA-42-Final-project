"""Pipeline A converter: Nemotron plain-text summary -> normalized Incident JSON.

Consumes ONLY the ``summary_output`` field of a Nemotron summary JSON (never
``internal_thinking``) and asks Gemma to convert it into the shared normalized
contract (scripts/incident_contract.py) with source_pipeline "nemotron_gemma".

Gemma produces observations only; duration and all envelope fields are computed
deterministically in Python. Gemma does not make notification decisions.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
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

DEFAULT_MODEL = "gemma-4-26b-a4b-it"


def build_prompt(summary_text: str, ppe_items: list[str]) -> str:
    scope = ", ".join(ppe_items)
    return f"""
[SYSTEM DIRECTIVE: Convert a plain-text workplace-safety summary into ONE strict
JSON object. Output ONLY the raw JSON object: no markdown fences, no reasoning.]

You are given a plain-text safety summary describing a video. Analyze these PPE
items only: {scope}.

Produce one incident per PPE item per confirmed period during which that item
was MISSING (the body area was visible and the item was not worn).

Rules:
- Use only information explicitly present in the summary. Do not invent events.
- Allowed status values: present, missing, unknown, not_applicable.
- If visibility is not stated for an item, treat it as unknown - NOT missing.
- Only emit an incident when an item is clearly missing.
- Times are numeric seconds (floats). Convert mm:ss to seconds.
- If the summary says the item was put back on, set end_seconds to that time.
- If absence was confirmed but never resolved, set end_seconds to null and, if
  possible, set minimum_confirmed_duration_seconds to the last confirmed second
  of absence minus the start.
- Do not compute duration yourself. Do not decide notifications.

Return exactly this JSON structure and nothing else:
{{
  "summary": "short factual summary",
  "incidents": [
    {{
      "ppe_item": "hard_hat",
      "status": "missing",
      "start_seconds": 13.0,
      "end_seconds": 33.0,
      "minimum_confirmed_duration_seconds": null,
      "confidence": 0.9,
      "action_sequence": [
        {{
          "event": "ppe_removed",
          "ppe_item": "hard_hat",
          "timestamp_seconds": 13.0,
          "description": "Worker removes the hard hat."
        }}
      ]
    }}
  ]
}}

Summary text to convert:
\"\"\"
{summary_text}
\"\"\"
""".strip()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a Nemotron plain-text summary JSON into normalized "
            "Incident JSON using Gemma (Pipeline A)."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Nemotron summary JSON produced by native_video_pipeline.py.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the normalized Incident JSON.",
    )
    parser.add_argument(
        "--video-id",
        required=True,
        help="Logical video id to embed in the output.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=(
            "Gemma model name. Precedence: --model, then GOOGLE_GEMMA_MODEL, "
            f"then '{DEFAULT_MODEL}'."
        ),
    )
    parser.add_argument(
        "--ppe-items",
        default=None,
        help=f"Comma-separated PPE scope. Default: {','.join(PPE_ITEMS)}.",
    )
    return parser.parse_args()


def resolve_model(cli_model: str | None) -> str:
    if cli_model:
        return cli_model
    return os.getenv("GOOGLE_GEMMA_MODEL", DEFAULT_MODEL)


def load_summary_text(input_path: Path) -> str:
    """Read only ``summary_output``. ``internal_thinking`` is never touched."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input summary not found: {input_path}")

    data = json.loads(input_path.read_text(encoding="utf-8"))
    summary_text = data.get("summary_output")

    if not isinstance(summary_text, str) or not summary_text.strip():
        raise ValueError(
            "The Nemotron summary JSON does not contain a non-empty "
            "'summary_output' field."
        )
    return summary_text.strip()


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
    """Deterministically build the normalized document from Gemma output."""
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
        source_pipeline="nemotron_gemma",
        models=["nemotron", model],
        analysis_scope=ppe_items,
        incidents=incidents,
        summary=summary,
        quality=default_quality(parse_success=True, warnings=warnings),
    )


def diagnostic_path_for(output_path: Path) -> Path:
    return output_path.with_name(f"{output_path.stem}_diagnostic.json")


def save_diagnostic(
    output_path: Path,
    model: str,
    input_file: str,
    model_text: str,
    parse_success: bool,
    parse_error: str | None,
) -> Path:
    diagnostic = {
        "model": model,
        "input_file": input_file,
        "model_text": model_text,
        "parse_success": parse_success,
        "parse_error": parse_error,
    }
    path = diagnostic_path_for(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(diagnostic, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def call_gemma(model: str, api_key: str, prompt: str) -> str:
    from google import genai

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model, contents=[prompt])
    return response.text or ""


def main() -> None:
    args = parse_arguments()
    model = resolve_model(args.model)
    ppe_items = parse_ppe_items(args.ppe_items)

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Fail clearly before any API request if the summary is missing/empty.
    summary_text = load_summary_text(input_path)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY environment variable not found.")

    prompt = build_prompt(summary_text, ppe_items)
    model_text = call_gemma(model, api_key, prompt)

    parse_success = True
    parse_error: str | None = None
    parsed_result: dict[str, Any] = {}
    try:
        parsed_result = extract_json(model_text)
    except ValueError as error:
        parse_success = False
        parse_error = str(error)

    diagnostic_path = save_diagnostic(
        output_path=output_path,
        model=model,
        input_file=str(input_path),
        model_text=model_text,
        parse_success=parse_success,
        parse_error=parse_error,
    )
    print(f"Diagnostic saved: {diagnostic_path}")

    if not parse_success:
        print(
            "\n[PARSE FAILURE] Gemma response could not be parsed as JSON: "
            f"{parse_error}"
        )
        sys.exit(1)

    document = assemble_document(parsed_result, args.video_id, model, ppe_items)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Incident JSON saved: {output_path}")
    print(f"Incident detected: {document['incident_detected']}")
    print(f"Incident count: {len(document['incidents'])}")


if __name__ == "__main__":
    main()
