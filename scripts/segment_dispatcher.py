"""Segment Dispatcher: bounded worker pool feeding finalized event segments
into Pipeline A (Nemotron -> Gemma, unchanged) and then into the Incident
State Manager / Evidence Manager. Replaces the old single-threaded
subprocess-per-fixed-chunk worker used by the fixed 10-second design.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING

sys.path.insert(0, str(Path(__file__).resolve().parent))
from active_buffer_manager import FinalizedSegment
from evidence_manager import EvidenceManager
from incident_state_manager import IncidentStateManager

if TYPE_CHECKING:
    from telegram_notifier import TelegramNotifier

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_PIPELINE_A = REPO_ROOT / "scripts" / "run_pipeline_a.py"


class SegmentDispatcher:
    """Dispatches finalized segments to Pipeline A concurrently, bounded by
    max_workers, then stitches results into the running incident timeline."""

    def __init__(
        self,
        state_manager: IncidentStateManager,
        evidence_manager: EvidenceManager,
        output_dir: str | Path,
        failed_dir: str | Path,
        max_workers: int = 3,
        gemma_model: str | None = None,
        ppe_items: str | None = None,
        notifier: "TelegramNotifier | None" = None,
    ) -> None:
        self.state_manager = state_manager
        self.evidence_manager = evidence_manager
        self.output_dir = Path(output_dir)
        self.failed_dir = Path(failed_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.failed_dir.mkdir(parents=True, exist_ok=True)

        self.gemma_model = gemma_model
        self.ppe_items = ppe_items
        self._notifier = notifier
        self._pool = ThreadPoolExecutor(max_workers=max_workers)

    def submit(self, segment: FinalizedSegment) -> None:
        self._pool.submit(self._process, segment)

    def shutdown(self, wait: bool = True) -> None:
        self._pool.shutdown(wait=wait)

    def _process(self, segment: FinalizedSegment) -> None:
        command = [
            sys.executable,
            str(RUN_PIPELINE_A),
            "--video-path",
            str(segment.path),
            "--output-dir",
            str(self.output_dir),
        ]
        if self.ppe_items:
            command += ["--ppe-items", self.ppe_items]
        if self.gemma_model:
            command += ["--model", self.gemma_model]

        result = subprocess.run(
            command, cwd=str(REPO_ROOT), capture_output=True, text=True
        )

        if result.returncode != 0:
            # Covers every Pipeline A failure mode, including a Nemotron
            # timeout that survived retries in native_video_pipeline.py --
            # the segment is preserved for inspection/retry and processing
            # of future events continues uninterrupted.
            logger.error(
                "[DISPATCHER] Pipeline A failed for %s (exit %d); "
                "segment preserved for retry.",
                segment.path.name,
                result.returncode,
            )
            if (result.stderr or "").strip():
                logger.error(result.stderr.strip())
            self._move_to_failed(segment)
            return

        stdout_lines = (result.stdout or "").strip().splitlines()
        incident_path = Path(stdout_lines[-1]) if stdout_lines else None

        if not incident_path or not incident_path.exists():
            logger.error(
                "[DISPATCHER] Pipeline A reported success but no incident "
                "file was found for %s.",
                segment.path.name,
            )
            self._move_to_failed(segment)
            return

        try:
            merged_document, touched_incident_ids = self.state_manager.ingest_segment(
                incident_json_path=incident_path,
                segment=segment,
            )
        except ValueError as validation_error:
            logger.error(
                "[DISPATCHER] Segment %s produced an invalid document and "
                "was skipped: %s",
                segment.path.name,
                validation_error,
            )
            self._move_to_failed(segment)
            return

        self.evidence_manager.attach_evidence(
            document=merged_document,
            segment=segment,
            touched_incident_ids=touched_incident_ids,
        )

        self.state_manager.persist(merged_document)

        if self._notifier is not None:
            self._notifier.notify_if_needed(merged_document)

        logger.info(
            "[DISPATCHER] Segment %s (%.1fs) merged. Open incidents: %d; "
            "Total incidents: %d",
            segment.path.name,
            segment.duration_seconds,
            self.state_manager.open_incident_count(),
            len(merged_document["incidents"]),
        )

    def _move_to_failed(self, segment: FinalizedSegment) -> None:
        try:
            target = self.failed_dir / segment.path.name
            segment.path.replace(target)
            logger.info("[DISPATCHER] Moved failed segment to %s", target)
        except OSError as move_error:
            logger.error("[DISPATCHER] Could not move failed segment: %s", move_error)
