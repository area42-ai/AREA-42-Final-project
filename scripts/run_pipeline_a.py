"""Single entry point for Pipeline A (Nemotron -> Gemma), end-to-end.

Usage (named video already in data/test/, original batch flow):
    python scripts/run_pipeline_a.py --video-name <name> --output-dir <dir> \
        [--ppe-items hard_hat,safety_vest,safety_glasses,gloves] [--model <gemma-model>]

Usage (arbitrary video path, e.g. an event-driven segment produced by the
live pipeline, not necessarily inside data/test/):
    python scripts/run_pipeline_a.py --video-path <path> --output-dir <dir> \
        [--ppe-items ...] [--model ...]

Exactly one of --video-name / --video-path must be given.

  Stage 1  scripts/native_video_pipeline.py   (video -> plain-text summary)
  Stage 2  scripts/gemma_text_to_incident.py  (summary -> normalized Incident JSON,
                                                via the Gemma API)

It does not modify either stage's model logic. All diagnostics/warnings/errors
are logged; on success, stdout contains ONLY the final incident JSON path.

--model applies to the Gemma conversion stage (Stage 2). The Nemotron model
used in Stage 1 is controlled by the NVIDIA_NEMOTRON_MODEL environment
variable.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
import os


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
DATA_TEST_DIR = REPO_ROOT / "data" / "test"

NATIVE_SCRIPT = SCRIPTS_DIR / "native_video_pipeline.py"
GEMMA_SCRIPT = SCRIPTS_DIR / "gemma_text_to_incident.py"

logger = logging.getLogger(__name__)

# Environment variables required to run Pipeline A end-to-end.
REQUIRED_ENV_VARS = {
    "NVIDIA_API_KEY": "Stage 1 (Nemotron whole-video analysis)",
    "GOOGLE_API_KEY": "Stage 2 (Gemma text-to-JSON conversion)",
}

# Packages that indicate the project virtual environment is in use.
REQUIRED_IMPORTS = ("cv2", "openai")


def venv_activation_hint() -> str:
    return (
        "This does not look like the project virtual environment.\n"
        "Activate it first, then re-run:\n"
        "    .\\.venv\\Scripts\\Activate.ps1        (Windows PowerShell)\n"
        "    source .venv/bin/activate            (macOS/Linux)\n"
        "Or invoke the venv Python directly, e.g.:\n"
        "    .\\.venv\\Scripts\\python.exe scripts\\run_pipeline_a.py ..."
    )


def check_environment_imports() -> None:
    missing = [
        name
        for name in REQUIRED_IMPORTS
        if importlib.util.find_spec(name) is None
    ]
    if missing:
        logger.error(
            "Missing required Python package(s): %s.\n%s",
            ", ".join(missing),
            venv_activation_hint(),
        )
        raise SystemExit(1)


def check_required_env_vars() -> None:
    missing = [
        name for name in REQUIRED_ENV_VARS if not os.getenv(name)
    ]
    if missing:
        lines = ["Missing required environment variable(s):"]
        for name in missing:
            lines.append(f"  - {name}  (needed for {REQUIRED_ENV_VARS[name]})")
        lines.append("")
        lines.append(
            "Create a .env file in the project root (copy .env.example) and add "
            "the value(s):"
        )
        lines.append("    copy .env.example .env        (Windows)")
        lines.append("    cp .env.example .env           (macOS/Linux)")
        lines.append("Then set each variable in .env, for example:")
        for name in missing:
            lines.append(f"    {name}=your_value_here")
        logger.error("\n".join(lines))
        raise SystemExit(1)


def resolve_video_path(video_name: str) -> Path:
    candidate = DATA_TEST_DIR / video_name
    if candidate.exists():
        return candidate

    lines = [
        f"Video not found: {candidate}",
        "",
        f"Files currently in {DATA_TEST_DIR}:",
    ]
    if DATA_TEST_DIR.exists():
        entries = sorted(
            entry.name for entry in DATA_TEST_DIR.iterdir() if entry.is_file()
        )
        if entries:
            lines.extend(f"  - {name}" for name in entries)
        else:
            lines.append("  (no files)")
    else:
        lines.append(f"  (directory does not exist: {DATA_TEST_DIR})")
    logger.error("\n".join(lines))
    raise SystemExit(1)


def resolve_explicit_video_path(video_path: str) -> Path:
    candidate = Path(video_path)
    if not candidate.is_absolute():
        candidate = (REPO_ROOT / candidate).resolve()
    if not candidate.exists():
        logger.error("Video not found at explicit --video-path: %s", candidate)
        raise SystemExit(1)
    return candidate


def check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        logger.warning(
            "ffmpeg is not on PATH. Videos over 5MB will be sent "
            "uncompressed (slower and more expensive), but the run will "
            "continue."
        )


def run_stage(command: list[str], stage_label: str) -> subprocess.CompletedProcess:
    result = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("%s failed (exit code %d).", stage_label, result.returncode)
        stderr_text = (result.stderr or "").strip()
        stdout_text = (result.stdout or "").strip()
        if stderr_text:
            logger.error("--- stderr ---\n%s", stderr_text)
        elif stdout_text:
            logger.error("--- output ---\n%s", stdout_text)
        raise SystemExit(result.returncode)
    return result


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run Pipeline A end-to-end: Nemotron whole-video summary followed "
            "by Gemma text-to-JSON conversion into the normalized contract."
        )
    )
    video_group = parser.add_mutually_exclusive_group(required=True)
    video_group.add_argument(
        "--video-name",
        default=None,
        help="Video filename inside data/test/ (e.g. worker_removes_helmet.mp4).",
    )
    video_group.add_argument(
        "--video-path",
        default=None,
        help=(
            "Full/relative path to a video anywhere on disk (e.g. an "
            "event-driven segment produced by the live pipeline). Use this "
            "instead of --video-name when the file is not inside data/test/."
        ),
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for the Nemotron summary and the final incident JSON.",
    )
    parser.add_argument(
        "--ppe-items",
        default=None,
        help=(
            "Comma-separated PPE scope passed to both stages. "
            "Default: the full PPE set."
        ),
    )
    parser.add_argument(
        "--model",
        default=None,
        help=(
            "Gemma model for Stage 2 (conversion). The Stage 1 Nemotron model "
            "is set by the NVIDIA_NEMOTRON_MODEL environment variable."
        ),
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    args = parse_arguments()

    # --- Environment checks (before any work) ---
    check_environment_imports()
    load_dotenv(dotenv_path=REPO_ROOT / ".env")
    check_required_env_vars()

    if args.video_path:
        video_path = resolve_explicit_video_path(args.video_path)
    else:
        video_path = resolve_video_path(args.video_name)

    check_ffmpeg()

    stem = video_path.stem
    output_dir = Path(args.output_dir)
    abs_output_dir = (
        output_dir if output_dir.is_absolute() else REPO_ROOT / output_dir
    )
    abs_output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = abs_output_dir / f"nemotron_{stem}_summary.json"
    final_incident_path = abs_output_dir / f"{stem}_pipeline_a_incident.json"

    # --- Stage 1: Nemotron whole-video -> plain-text summary ---
    stage1_command = [sys.executable, str(NATIVE_SCRIPT)]
    if args.video_path:
        stage1_command += ["--video-path", str(video_path)]
    else:
        stage1_command += [args.video_name]
    stage1_command += ["--output-dir", args.output_dir]
    if args.ppe_items:
        stage1_command += ["--ppe-items", args.ppe_items]
    run_stage(stage1_command, "Stage 1 (native_video_pipeline.py)")

    # --- Locate and validate the Nemotron summary ---
    if not summary_path.exists():
        logger.error(
            "Stage 1 finished but the expected summary file was not found: %s",
            summary_path,
        )
        raise SystemExit(1)
    if summary_path.stat().st_size == 0:
        logger.error("Stage 1 produced an empty summary file: %s", summary_path)
        raise SystemExit(1)
    try:
        summary_data = json.loads(summary_path.read_text(encoding="utf-8"))
    except ValueError as error:
        logger.error(
            "Stage 1 summary file is not valid JSON: %s\n%s", summary_path, error
        )
        raise SystemExit(1)
    summary_text = summary_data.get("summary_output")
    if not isinstance(summary_text, str) or not summary_text.strip():
        logger.error(
            "Stage 1 summary has no usable 'summary_output' text (the model "
            "returned nothing to convert): %s",
            summary_path,
        )
        raise SystemExit(1)

    # --- Stage 2: summary -> normalized Incident JSON ---
    stage2_command = [
        sys.executable,
        str(GEMMA_SCRIPT),
        "--input",
        str(summary_path),
        "--output",
        str(final_incident_path),
        "--video-id",
        stem,
    ]
    if args.ppe_items:
        stage2_command += ["--ppe-items", args.ppe_items]
    if args.model:
        stage2_command += ["--model", args.model]
    run_stage(stage2_command, "Stage 2 (gemma_text_to_incident.py)")

    if not final_incident_path.exists():
        logger.error(
            "Stage 2 finished but the final incident file was not found: %s",
            final_incident_path,
        )
        raise SystemExit(1)

    # Trigger Telegram notifications if any incidents were detected
    warn("\nTriggering Telegram notification bot...")
    try:
        subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "send_notification_bot.py"),
                "--input",
                str(final_incident_path),
            ],
            stdout=sys.stderr,
            stderr=sys.stderr,
            check=False,
        )
    except Exception as notify_err:
        warn(f"Failed to run notification bot: {notify_err}")

    # Success: stdout carries ONLY the final incident JSON path.
    print(str(final_incident_path))


if __name__ == "__main__":
    main()
