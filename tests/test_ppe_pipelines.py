"""Offline self-tests for the AREA-42 full-PPE pipelines.

No API calls, no video processing, no secrets. Exercises the pure logic of the
shared contract and the four pipelines. Run with:

    python tests/test_ppe_pipelines.py

(Use the interpreter that has opencv/requests installed, e.g. the repo .venv,
since importing video_frame_pipeline imports cv2.)
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import incident_contract as contract
import gemma_text_to_incident as gti
import gemma_video_pipeline as gvp
import video_frame_pipeline as vfp


def _make_frame(
    tmp: Path,
    index: int,
    timestamp: float,
    statuses: dict[str, str],
    analysis_status: str = "success",
) -> dict:
    frames_dir = tmp / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    frame_path = frames_dir / f"frame_{index:04d}.jpg"
    frame_path.write_bytes(b"\xff\xd8\xff\xd9")  # minimal placeholder bytes
    ppe = {
        item: {"status": status, "confidence": "high", "evidence": "test"}
        for item, status in statuses.items()
    }
    return {
        "timestamp_seconds": timestamp,
        "frame_index": index,
        "frame_path": str(frame_path),
        "analysis_status": analysis_status,
        "person_visible": True,
        "ppe": ppe,
    }


# 1. Four-PPE frame response normalizes correctly.
def test_four_ppe_frame_normalizes():
    raw = {
        "person_visible": True,
        "ppe": {
            "hard_hat": {"status": "present", "confidence": "high"},
            "safety_vest": {"status": "worn", "confidence": "medium"},
            "safety_glasses": {"status": "missing", "confidence": "low"},
            "gloves": {"status": "unknown", "confidence": "low"},
        },
    }
    out = vfp.normalize_frame(raw, list(contract.PPE_ITEMS))
    assert out["ppe"]["hard_hat"]["status"] == "present"
    assert out["ppe"]["safety_vest"]["status"] == "present"  # alias worn
    assert out["ppe"]["safety_glasses"]["status"] == "missing"
    assert out["ppe"]["gloves"]["status"] == "unknown"


# 2. Invisible hands -> gloves unknown.
def test_invisible_hands_gloves_unknown():
    raw = {"person_visible": True, "ppe": {"hard_hat": {"status": "present"}}}
    out = vfp.normalize_frame(raw, list(contract.PPE_ITEMS))
    assert out["ppe"]["gloves"]["status"] == "unknown"  # omitted -> unknown
    raw2 = {"ppe": {"gloves": {"status": "not_visible"}}}
    out2 = vfp.normalize_frame(raw2, ["gloves"])
    assert out2["ppe"]["gloves"]["status"] == "unknown"


# 3. Invisible eyes -> safety_glasses unknown.
def test_invisible_eyes_glasses_unknown():
    raw = {"ppe": {"safety_glasses": {"status": "unclear"}}}
    out = vfp.normalize_frame(raw, ["safety_glasses"])
    assert out["ppe"]["safety_glasses"]["status"] == "unknown"


# 4. Missing gloves for two consecutive frames opens a gloves incident.
def test_two_missing_opens_incident():
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        frames = [
            _make_frame(tmp, 0, 1.0, {"gloves": "missing"}),
            _make_frame(tmp, 1, 2.0, {"gloves": "missing"}),
        ]
        incidents = vfp.build_item_incidents(
            item="gloves",
            frame_results=frames,
            evidence_dir=tmp / "evidence",
            confirmation_frames=2,
        )
        assert len(incidents) == 1
        assert incidents[0]["ppe_item"] == "gloves"
        assert incidents[0]["status"] == contract.STATUS_UNRESOLVED


# 5. Missing glasses and gloves simultaneously creates two incidents.
def test_two_items_missing_two_incidents():
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        statuses = {"safety_glasses": "missing", "gloves": "missing"}
        frames = [
            _make_frame(tmp, 0, 1.0, statuses),
            _make_frame(tmp, 1, 2.0, statuses),
        ]
        incidents = vfp.build_all_incidents(
            frame_results=frames,
            evidence_dir=tmp / "evidence",
            confirmation_frames=2,
            ppe_items=["safety_glasses", "gloves"],
        )
        assert len(incidents) == 2
        items = {inc["ppe_item"] for inc in incidents}
        assert items == {"safety_glasses", "gloves"}


# 6. An unknown frame does not close an active incident.
def test_unknown_does_not_close():
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        frames = [
            _make_frame(tmp, 0, 1.0, {"gloves": "missing"}),
            _make_frame(tmp, 1, 2.0, {"gloves": "missing"}),
            _make_frame(tmp, 2, 3.0, {"gloves": "unknown"}),
            _make_frame(tmp, 3, 4.0, {"gloves": "unknown"}),
        ]
        incidents = vfp.build_item_incidents(
            item="gloves",
            frame_results=frames,
            evidence_dir=tmp / "evidence",
            confirmation_frames=2,
        )
        assert len(incidents) == 1
        assert incidents[0]["status"] == contract.STATUS_UNRESOLVED
        assert incidents[0]["end_seconds"] is None


# 7. Two present frames close the correct PPE incident.
def test_two_present_closes():
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        frames = [
            _make_frame(tmp, 0, 1.0, {"gloves": "missing"}),
            _make_frame(tmp, 1, 2.0, {"gloves": "missing"}),
            _make_frame(tmp, 2, 3.0, {"gloves": "present"}),
            _make_frame(tmp, 3, 4.0, {"gloves": "present"}),
        ]
        incidents = vfp.build_item_incidents(
            item="gloves",
            frame_results=frames,
            evidence_dir=tmp / "evidence",
            confirmation_frames=2,
        )
        assert len(incidents) == 1
        assert incidents[0]["status"] == contract.STATUS_RESOLVED
        assert incidents[0]["end_seconds"] == 3.0


# 8. Start time uses the first frame of the confirmation streak.
def test_start_uses_first_frame():
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        frames = [
            _make_frame(tmp, 0, 1.0, {"gloves": "missing"}),
            _make_frame(tmp, 1, 2.0, {"gloves": "missing"}),
            _make_frame(tmp, 2, 3.0, {"gloves": "missing"}),
        ]
        incidents = vfp.build_item_incidents(
            item="gloves",
            frame_results=frames,
            evidence_dir=tmp / "evidence",
            confirmation_frames=2,
        )
        assert incidents[0]["start_seconds"] == 1.0


# 9. An unresolved incident has duration null (normalized).
def test_unresolved_duration_null():
    incident = contract.build_incident(
        index=1,
        ppe_items=["gloves"],
        start_seconds=1.0,
        end_seconds=None,
        status=contract.STATUS_UNRESOLVED,
        minimum_confirmed_duration_seconds=2.0,
    )
    assert incident["end_seconds"] is None
    assert incident["duration_seconds"] is None
    assert incident["minimum_confirmed_duration_seconds"] == 2.0


# 10. The Nemotron converter never reads internal_thinking.
def test_converter_ignores_internal_thinking():
    with tempfile.TemporaryDirectory() as tmp_name:
        summary_file = Path(tmp_name) / "summary.json"
        summary_file.write_text(
            json.dumps(
                {
                    "summary_output": "Worker removed the hard hat at 00:13.",
                    "internal_thinking": "SECRET_SHOULD_NOT_LEAK",
                }
            ),
            encoding="utf-8",
        )
        text = gti.load_summary_text(summary_file)
        assert "SECRET_SHOULD_NOT_LEAK" not in text
        prompt = gti.build_prompt(text, ["hard_hat"])
        assert "SECRET_SHOULD_NOT_LEAK" not in prompt


# 11. Gemma duration is recalculated by Python.
def test_gemma_duration_recalculated():
    parsed = {
        "summary": "hat off then on",
        "incidents": [
            {
                "ppe_item": "hard_hat",
                "status": "missing",
                "start_seconds": 13.0,
                "end_seconds": 33.0,
                "duration_seconds": 999.0,  # bogus model value, must be ignored
                "confidence": 0.9,
            }
        ],
    }
    doc = gti.assemble_document(parsed, "vid", "gemma-4-26b-a4b-it", ["hard_hat"])
    incident = doc["incidents"][0]
    assert incident["duration_seconds"] == 20.0
    assert incident["start_seconds"] == 13.0 and incident["end_seconds"] == 33.0


# 12. All three normalized outputs pass common validation.
def test_all_three_outputs_validate():
    parsed = {
        "summary": "test",
        "incidents": [
            {
                "ppe_item": "safety_glasses",
                "status": "missing",
                "start_seconds": 2.0,
                "end_seconds": 6.0,
                "confidence": 0.8,
            }
        ],
    }
    scope = list(contract.PPE_ITEMS)

    nemotron_gemma = gti.assemble_document(parsed, "vid", "gemma-x", scope)
    gemma_direct = gvp.assemble_document(parsed, "vid", "gemma-x", scope)

    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        frames = [
            _make_frame(tmp, 0, 1.0, {"gloves": "missing"}),
            _make_frame(tmp, 1, 2.0, {"gloves": "missing"}),
            _make_frame(tmp, 2, 3.0, {"gloves": "present"}),
            _make_frame(tmp, 3, 4.0, {"gloves": "present"}),
        ]
        incidents = vfp.build_all_incidents(
            frame_results=frames,
            evidence_dir=tmp / "evidence",
            confirmation_frames=2,
            ppe_items=["gloves"],
        )
        quality = vfp.build_quality(frames, len(frames))
        llama_direct = vfp.build_normalized_document(
            video_path=Path("vid.mp4"),
            model="llama-x",
            ppe_items=["gloves"],
            incidents=incidents,
            quality=quality,
        )

    assert contract.validate_document(nemotron_gemma) == []
    assert contract.validate_document(gemma_direct) == []
    assert contract.validate_document(llama_direct) == []
    assert nemotron_gemma["source_pipeline"] == "nemotron_gemma"
    assert gemma_direct["source_pipeline"] == "gemma_direct"
    assert llama_direct["source_pipeline"] == "llama_direct"


# 13. Model refusal remains distinct from parse_error.
def test_refusal_distinct_from_parse_error():
    refusal = "I'm not going to engage in this conversation topic."
    assert vfp.is_refusal(refusal) is True
    # A refusal is not valid JSON, but it is classified as refusal BEFORE
    # parsing is attempted, so it never becomes a parse_error.
    raised = False
    try:
        vfp.extract_json(refusal)
    except ValueError:
        raised = True
    assert raised
    # A malformed-JSON string is not a refusal.
    assert vfp.is_refusal("{ broken json") is False


# 14. Timeout/retry/checkpoint behavior remains intact.
def test_retry_and_checkpoint_helpers():
    # Exponential backoff without a Retry-After header.
    assert vfp.retry_delay_seconds(None, 2.0, 0) == 2.0
    assert vfp.retry_delay_seconds(None, 2.0, 1) == 4.0

    class _Resp:
        headers = {"Retry-After": "7"}

    assert vfp.retry_delay_seconds(_Resp(), 2.0, 3) == 7.0

    # Atomic checkpoint write.
    with tempfile.TemporaryDirectory() as tmp_name:
        target = Path(tmp_name) / "frame_results.json"
        vfp.write_json(target, [{"a": 1}])
        assert json.loads(target.read_text(encoding="utf-8")) == [{"a": 1}]
        assert not target.with_suffix(".json.tmp").exists()


TESTS = [
    ("four_ppe_frame_normalizes", test_four_ppe_frame_normalizes),
    ("invisible_hands_gloves_unknown", test_invisible_hands_gloves_unknown),
    ("invisible_eyes_glasses_unknown", test_invisible_eyes_glasses_unknown),
    ("two_missing_opens_incident", test_two_missing_opens_incident),
    ("two_items_missing_two_incidents", test_two_items_missing_two_incidents),
    ("unknown_does_not_close", test_unknown_does_not_close),
    ("two_present_closes", test_two_present_closes),
    ("start_uses_first_frame", test_start_uses_first_frame),
    ("unresolved_duration_null", test_unresolved_duration_null),
    ("converter_ignores_internal_thinking", test_converter_ignores_internal_thinking),
    ("gemma_duration_recalculated", test_gemma_duration_recalculated),
    ("all_three_outputs_validate", test_all_three_outputs_validate),
    ("refusal_distinct_from_parse_error", test_refusal_distinct_from_parse_error),
    ("retry_and_checkpoint_helpers", test_retry_and_checkpoint_helpers),
]


def main() -> None:
    failures = 0
    for name, test in TESTS:
        try:
            test()
            print(f"PASS  {name}")
        except AssertionError as error:
            failures += 1
            print(f"FAIL  {name}: {error}")
        except Exception as error:  # noqa: BLE001
            failures += 1
            print(f"ERROR {name}: {type(error).__name__}: {error}")

    total = len(TESTS)
    print(f"\n{total - failures}/{total} tests passed.")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
