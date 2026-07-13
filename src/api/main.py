"""AREA-42 Watch Out API - FastAPI backend entrypoint."""
from pathlib import Path
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AREA-42 Watch Out API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LIVE_DIR = PROJECT_ROOT / "outputs" / "live"
SETTINGS_PATH = PROJECT_ROOT / "configs" / "settings.json"
ALLOWED_LANGUAGES = {"en", "ru", "az"}


def list_camera_ids() -> list[str]:
    if not LIVE_DIR.exists():
        return []
    return sorted(p.name for p in LIVE_DIR.iterdir() if p.is_dir())


def load_camera_document(camera_id: str) -> dict:
    path = LIVE_DIR / camera_id / "normalized_incident.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"No data for camera '{camera_id}'")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {"language": "en"}
    with open(SETTINGS_PATH, encoding="utf-8") as f:
        return json.load(f)


def write_settings(data: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class LanguageUpdate(BaseModel):
    language: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/cameras")
def get_cameras():
    cameras = []
    for camera_id in list_camera_ids():
        try:
            doc = load_camera_document(camera_id)
            cameras.append({
                "camera_id": camera_id,
                "video_id": doc.get("video_id"),
                "incident_detected": doc.get("incident_detected"),
                "incident_count": len(doc.get("incidents", [])),
            })
        except HTTPException:
            continue
    return cameras


@app.get("/api/incidents")
def get_incidents():
    all_incidents = []
    for camera_id in list_camera_ids():
        try:
            doc = load_camera_document(camera_id)
        except HTTPException:
            continue
        for incident in doc.get("incidents", []):
            enriched = dict(incident)
            enriched["camera_id"] = camera_id
            enriched["id"] = f"{camera_id}:{incident['incident_id']}"
            enriched["video_id"] = doc.get("video_id")
            all_incidents.append(enriched)
    return all_incidents


@app.get("/api/incidents/{composite_id}")
def get_incident(composite_id: str):
    if ":" not in composite_id:
        raise HTTPException(status_code=400, detail="Expected format: {camera_id}:{incident_id}")
    camera_id, incident_id = composite_id.split(":", 1)
    doc = load_camera_document(camera_id)
    for incident in doc.get("incidents", []):
        if incident["incident_id"] == incident_id:
            enriched = dict(incident)
            enriched["camera_id"] = camera_id
            enriched["id"] = composite_id
            enriched["video_id"] = doc.get("video_id")
            enriched["summary"] = doc.get("summary")
            return enriched
    raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found on '{camera_id}'")


@app.get("/api/settings/language")
def get_language():
    return read_settings()


@app.post("/api/settings/language")
def set_language(payload: LanguageUpdate):
    if payload.language not in ALLOWED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Language must be one of {sorted(ALLOWED_LANGUAGES)}")
    write_settings({"language": payload.language})
    return {"language": payload.language}
