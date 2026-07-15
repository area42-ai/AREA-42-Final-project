"""YOLO-based PPE detection for frame annotation.

Lazy-loads melihuzunoglu/ppe-detection from HuggingFace on first call.
Annotates frames with colored bounding boxes: green for present PPE,
red for missing PPE. Gloves and boots classes are ignored.
"""

from __future__ import annotations

import numpy as np
import cv2

_model = None
_MODEL_REPO = "melihuzunoglu/ppe-detection"
_MODEL_FILE = "best.pt"

# Actual classes in melihuzunoglu/ppe-detection: helmet, human, no-helmet, vest
_COLORS: dict[str, tuple[int, int, int]] = {
    "helmet":    (0, 200, 0),    # green — compliant
    "vest":      (0, 200, 0),    # green — compliant
    "human":     (180, 180, 0),  # yellow — person box
    "no-helmet": (0, 0, 230),    # red — violation
}


def _get_model():
    global _model
    if _model is None:
        from ultralytics import YOLO
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(repo_id=_MODEL_REPO, filename=_MODEL_FILE)
        _model = YOLO(path)
    return _model


def annotate_frame(frame: np.ndarray) -> np.ndarray:
    """Return a copy of *frame* with YOLO PPE detection boxes drawn on it."""
    try:
        model = _get_model()
        results = model(frame, verbose=False, conf=0.35)[0]
        out = frame.copy()
        for box in results.boxes:
            cls_name = results.names[int(box.cls[0])]
            color = _COLORS.get(cls_name, (180, 180, 180))
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            label = f"{cls_name} {conf:.2f}"
            cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                out, label, (x1, max(y1 - 8, 14)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2,
            )
        return out
    except Exception:
        return frame
