import os
import sys
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, abort

LIVE_PIPELINE_PROCESS = None

# Load environment variables
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Try importing contract helpers (fallback if not available)
try:
    from incident_contract import (
        build_envelope,
        build_incident,
        PPE_ITEMS,
        STATUS_RESOLVED,
        STATUS_UNRESOLVED,
    )
except ImportError:
    # Inline fallback implementations of contract schema
    PPE_ITEMS = ("hard_hat", "safety_vest", "safety_glasses", "gloves")
    STATUS_RESOLVED = "resolved"
    STATUS_UNRESOLVED = "unresolved_after_last_confirmed_violation"
    
    def build_incident(*, index, ppe_item, start_seconds, end_seconds, status, **kwargs):
        return {
            "incident_id": f"incident_{index:03d}",
            "person_id": None,
            "status": status,
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "duration_seconds": (end_seconds - start_seconds) if (end_seconds is not None and start_seconds is not None) else None,
            "minimum_confirmed_duration_seconds": None,
            "violated_items": [ppe_item],
            "ppe_status": {item: ("missing" if item == ppe_item else "present") for item in PPE_ITEMS},
            "confidence": 0.85,
            "action_sequence": [],
            "evidence": []
        }
        
    def build_envelope(*, video_id, source_pipeline, models, analysis_scope, incidents, summary="", quality=None):
        return {
            "schema_version": "1.0",
            "video_id": video_id,
            "source_pipeline": source_pipeline,
            "models": models,
            "analysis_scope": analysis_scope,
            "incident_detected": len(incidents) > 0,
            "incidents": incidents,
            "summary": summary,
            "quality": quality or {"parse_success": True, "warnings": []}
        }

FRONTEND_DIR = REPO_ROOT / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")

# Register camera streaming blueprint
from camera_stream import camera_bp, release_camera
app.register_blueprint(camera_bp)

# Ensure data directory exists
DATA_TEST_DIR = REPO_ROOT / "data" / "test"
DATA_TEST_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = REPO_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# CORS Header configuration
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS,PUT,DELETE"
    return response

@app.route("/")
def serve_frontend():
    return send_from_directory(str(FRONTEND_DIR), "index.html")


@app.route("/api/videos", methods=["GET"])
def list_videos():
    try:
        # Scan for video files
        extensions = {".mp4", ".avi", ".mov", ".webm", ".mkv"}
        videos = [
            f.name
            for f in DATA_TEST_DIR.iterdir()
            if f.is_file() and f.suffix.lower() in extensions
        ]
        return jsonify({"videos": sorted(videos)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/upload", methods=["POST"])
def upload_video():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
        
    try:
        filename = Path(file.filename).name
        target_path = DATA_TEST_DIR / filename
        file.save(str(target_path))
        return jsonify({"filename": filename, "size": target_path.stat().st_size})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/analyze", methods=["POST"])
def analyze_video():
    data = request.get_json() or {}
    video_name = data.get("video_name")
    pipeline = data.get("pipeline", "pipeline_a")
    
    if not video_name:
        return jsonify({"error": "Missing 'video_name' in request body"}), 400
        
    video_path = DATA_TEST_DIR / video_name
    if not video_path.exists():
        return jsonify({"error": f"Video file '{video_name}' not found in data/test/"}), 404
        
    # Check if API keys are set to decide if we run live or simulated
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    is_live = bool(nvidia_key)
    
    if is_live:
        try:
            # Prepare commands and run pipeline script
            script_path = "run_pipeline_a.py"
            cmd = [
                sys.executable,
                str(script_path),
                "--video-name", video_name,
                "--output-dir", str(OUTPUT_DIR)
            ]
            
            # Run the process
            result = subprocess.run(
                cmd,
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            
            if result.returncode != 0:
                return jsonify({
                    "error": "Pipeline execution failed",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }), 500
                
            # The script outputs the path to the incident JSON on stdout
            output_file_path = result.stdout.strip()
            if not output_file_path or not Path(output_file_path).exists():
                # Fallback to look up by naming convention
                stem = Path(video_name).stem
                output_file_path = OUTPUT_DIR / f"{stem}_pipeline_a_incident.json"
                
            if Path(output_file_path).exists():
                with open(output_file_path, "r", encoding="utf-8") as f:
                    incident_json = json.load(f)
                return jsonify({
                    "mode": "live",
                    "data": incident_json
                })
            else:
                return jsonify({"error": "Pipeline finished but incident JSON not found."}), 500
                
        except Exception as e:
            return jsonify({"error": f"Error running pipeline: {str(e)}"}), 500
    else:
        # SIMULATION MODE
        # Return a realistic JSON contract response tailored to the video name
        stem = Path(video_name).stem.lower()
        
        incidents = []
        summary = ""
        
        if "helmet" in stem:
            # Helmet violation scenario
            incidents.append(
                build_incident(
                    index=1,
                    ppe_item="hard_hat",
                    start_seconds=6.5,
                    end_seconds=18.2,
                    status=STATUS_RESOLVED
                )
            )
            summary = (
                "A worker was detected entering the Zone A area without a hard hat at 00:06. "
                "The worker retrieved and put on their hard hat at 00:18, resolving the violation."
            )
        elif "vest" in stem:
            # Vest violation scenario
            incidents.append(
                build_incident(
                    index=1,
                    ppe_item="safety_vest",
                    start_seconds=0.0,
                    end_seconds=None,
                    status=STATUS_UNRESOLVED
                )
            )
            summary = (
                "The worker is missing a high-visibility safety vest for the entire duration of the footage. "
                "The violation remains unresolved."
            )
        elif "glasses" in stem or "goggles" in stem:
            # Glasses violation scenario
            incidents.append(
                build_incident(
                    index=1,
                    ppe_item="safety_glasses",
                    start_seconds=12.0,
                    end_seconds=22.5,
                    status=STATUS_RESOLVED
                )
            )
            summary = (
                "The worker removed their protective safety glasses at 00:12 while working near the grinding machine. "
                "They put their glasses back on at 00:22."
            )
        elif "compliant" in stem or "safe" in stem:
            # Fully compliant scenario
            incidents = []
            summary = "No safety violations detected. The worker wears a hard hat, safety vest, boots, and glasses during the entire video."
        else:
            # Default mock scenario (helmet missing briefly)
            incidents.append(
                build_incident(
                    index=1,
                    ppe_item="hard_hat",
                    start_seconds=5.0,
                    end_seconds=15.0,
                    status=STATUS_RESOLVED
                )
            )
            summary = (
                f"Simulated analysis for video '{video_name}'. A safety helmet was missing on worker 1 "
                "between 00:05 and 00:15. All other PPE items were present."
            )
            
        envelope = build_envelope(
            video_id=stem,
            source_pipeline="nemotron_gemma",
            models=["nvidia/nemotron-3-nano-omni-30b-a3b-reasoning", "gemma-4-26b-a4b-it"],
            analysis_scope=list(PPE_ITEMS),
            incidents=incidents,
            summary=summary
        )
        
        return jsonify({
            "mode": "simulated",
            "data": envelope
        })
    

def _resolve_evidence_url(inc: dict) -> str:
    """Return a /data/... URL for the first existing evidence file in an incident, or ''."""
    candidates = [inc.get("start_evidence_frame"), inc.get("last_seen_violation_frame")]
    for ev in inc.get("evidence", []):
        if isinstance(ev, dict):
            candidates.append(ev.get("path") or ev.get("frame_path"))
    for c in candidates:
        if not c:
            continue
        p = Path(c)
        if not p.is_absolute():
            p = REPO_ROOT / p
        if p.exists():
            try:
                rel = p.relative_to(REPO_ROOT / "data")
                return "/data/" + str(rel).replace("\\", "/")
            except ValueError:
                pass
    return ""


@app.route("/api/alerts")
def get_alerts():
    alerts = []
    logs_root = REPO_ROOT / "data" / "output_logs"
    if logs_root.exists():
        for timeline_file in logs_root.rglob("live_incident_timeline.json"):
            try:
                doc = json.loads(timeline_file.read_text(encoding="utf-8"))
                mtime = datetime.fromtimestamp(timeline_file.stat().st_mtime).isoformat()
                for inc in doc.get("incidents", []):
                    missing_items = inc.get("violated_items") or (
                        [inc["ppe_item"]] if inc.get("ppe_item") else []
                    )
                    alerts.append({
                        "id": inc.get("incident_id", ""),
                        "timestamp": inc.get("start_seconds") and mtime or mtime,
                        "description": (
                            f"{', '.join(missing_items) or 'PPE'} violation detected. "
                            f"{inc.get('worker_description', '')}".strip()
                        ),
                        "image_path": _resolve_evidence_url(inc),
                        "violators_details": [{"person_id": inc.get("person_id", 1), "missing": missing_items}],
                        "confidence": inc.get("confidence", 0.9),
                    })
            except Exception:
                continue
    alerts.sort(key=lambda a: a["timestamp"], reverse=True)
    return jsonify(alerts)


@app.route("/api/recordings")
def list_recordings():
    segs_root = REPO_ROOT / "data" / "event_segments"
    recordings = []
    if segs_root.exists():
        for f in sorted(segs_root.rglob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                rel = str(f.relative_to(REPO_ROOT / "data")).replace("\\", "/")
                recordings.append({
                    "filename": f.name,
                    "path": rel,
                    "url": "/data/" + rel,
                    "size": f.stat().st_size,
                    "duration": 0,
                    "timestamp": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                })
            except Exception:
                continue
    return jsonify(recordings)


@app.route("/data/<path:filename>")
def serve_data_file(filename):
    safe = REPO_ROOT / "data" / filename
    if not safe.resolve().is_relative_to((REPO_ROOT / "data").resolve()):
        abort(403)
    return send_from_directory(str(REPO_ROOT / "data"), filename)


@app.route("/api/live/start", methods=["POST"])
def start_live_monitoring():
    global LIVE_PIPELINE_PROCESS

    # Already running?
    if LIVE_PIPELINE_PROCESS and LIVE_PIPELINE_PROCESS.poll() is None:
        return jsonify({
            "success": False,
            "error": "Monitoring is already running."
        })

    script_path = REPO_ROOT / "scripts" / "live_stream_pipeline.py"

    # Release the browser preview capture so the pipeline subprocess can open the camera.
    # The preview will restart automatically on the next /api/stream/<id> request.
    cam_raw = os.getenv("CAMERA_SOURCE", "0")
    if str(cam_raw).isdigit():
        release_camera(int(cam_raw))

    try:
        LIVE_PIPELINE_PROCESS = subprocess.Popen(
            [
                sys.executable,
                str(script_path)
            ],
            cwd=REPO_ROOT
        )

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/live/stop", methods=["POST"])
def stop_live_monitoring():
    global LIVE_PIPELINE_PROCESS

    try:
        if LIVE_PIPELINE_PROCESS and LIVE_PIPELINE_PROCESS.poll() is None:
            LIVE_PIPELINE_PROCESS.terminate()
            LIVE_PIPELINE_PROCESS.wait(timeout=5)

        LIVE_PIPELINE_PROCESS = None

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500



if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Watch Out API Server starting on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=True)
