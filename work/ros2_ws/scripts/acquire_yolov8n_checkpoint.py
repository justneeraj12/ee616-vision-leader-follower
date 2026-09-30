#!/usr/bin/env python3
"""Acquire and fingerprint the named Ultralytics YOLOv8n checkpoint."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import ultralytics
from ultralytics import YOLO


WORKSPACE = Path("/workspace/work/ros2_ws")
MODEL_DIR = WORKSPACE / "models"
EVIDENCE_PATH = WORKSPACE / "results" / "yolo_dataset" / "pretrained_model.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint = MODEL_DIR / "yolov8n.pt"
    if not checkpoint.is_file():
        YOLO("yolov8n.pt")
        downloaded = Path.cwd() / "yolov8n.pt"
        if not downloaded.is_file():
            raise FileNotFoundError("Ultralytics did not create yolov8n.pt")
        downloaded.replace(checkpoint)
    YOLO(str(checkpoint))
    record = {
        "checkpoint": "yolov8n.pt",
        "license_context": "Ultralytics AGPL-3.0 distribution",
        "path": str(checkpoint),
        "provenance": "Acquired by Ultralytics YOLO API using the named yolov8n.pt checkpoint.",
        "scope": "training initialization only; not project detector evidence",
        "sha256": sha256(checkpoint),
        "size_bytes": checkpoint.stat().st_size,
        "source_url": (
            "https://github.com/ultralytics/assets/releases/download/"
            "v8.4.0/yolov8n.pt"
        ),
        "status": "pass",
        "ultralytics_version": ultralytics.__version__,
    }
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
