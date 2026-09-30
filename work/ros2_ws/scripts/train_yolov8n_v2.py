#!/usr/bin/env python3
"""Train corrective YOLOv8n v2 and derive validation-only range calibration."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import ultralytics
from ultralytics import YOLO


WORKSPACE = Path("/workspace/work/ros2_ws")
STARTING_WEIGHTS = WORKSPACE / "models" / "yolov8n.pt"
TRAINED_WEIGHTS = WORKSPACE / "models" / "yolov8n_predecessor_v2.pt"
DATASET_YAML = WORKSPACE / "experiments" / "yolov8n_gate" / "dataset_v2.yaml"
DATASET_ROOT = WORKSPACE / "datasets" / "ee616_predecessor_target_v2"
DATASET_MANIFEST = WORKSPACE / "results" / "yolo_dataset" / "dataset_v2_manifest.json"
RUN_ROOT = WORKSPACE / "results" / "yolo_training"
RUN_NAME = "run_20260929_corrective_v2"
EVIDENCE_ROOT = WORKSPACE / "results" / "yolo_gate"
FOCAL_PX = 640.0 / (2.0 * math.tan(1.2217304764 / 2.0))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _best_box(model: YOLO, image_path: Path):
    result = model.predict(
        source=str(image_path), imgsz=640, conf=0.25, iou=0.45,
        classes=[0], device=0, verbose=False,
    )[0]
    if result.boxes is None or len(result.boxes) == 0:
        return None
    confidences = result.boxes.conf.detach().cpu().numpy()
    index = int(np.argmax(confidences))
    return result.boxes.xyxy[index].detach().cpu().numpy()


def _image_level_test(model: YOLO) -> dict[str, Any]:
    images = sorted((DATASET_ROOT / "images" / "test").glob("*.png"))
    counts = {"true_positive": 0, "true_negative": 0, "false_positive": 0, "false_negative": 0}
    latencies = []
    model.predict(source=np.zeros((480, 640, 3), dtype=np.uint8), imgsz=640, conf=0.25, device=0, verbose=False)
    for image_path in images:
        label_path = DATASET_ROOT / "labels" / "test" / f"{image_path.stem}.txt"
        expected = bool(label_path.read_text(encoding="utf-8").strip())
        started = perf_counter()
        predicted = _best_box(model, image_path) is not None
        latencies.append((perf_counter() - started) * 1000.0)
        key = (
            "true_positive" if expected and predicted else
            "false_negative" if expected else
            "false_positive" if predicted else "true_negative"
        )
        counts[key] += 1
    latencies.sort()
    p95_index = max(0, math.ceil(0.95 * len(latencies)) - 1)
    return {
        **counts,
        "image_count": len(images),
        "latency_median_ms": float(np.median(latencies)),
        "latency_p95_ms": latencies[p95_index],
    }


def _validation_calibration(model: YOLO) -> dict[str, Any]:
    raw_ranges = []
    true_ranges = []
    metadata_paths = sorted((DATASET_ROOT / "metadata").glob("val_*.json"))
    for metadata_path in metadata_paths:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        for record in metadata["records"]:
            if not record["positive_label"]:
                continue
            label_path = DATASET_ROOT / record["label"]
            fields = label_path.read_text(encoding="utf-8").split()
            if len(fields) != 5:
                continue
            cx, cy, width, height = (float(value) for value in fields[1:])
            if cx - width / 2.0 <= 0.005 or cx + width / 2.0 >= 0.995:
                continue
            if cy - height / 2.0 <= 0.005 or cy + height / 2.0 >= 0.995:
                continue
            box = _best_box(model, DATASET_ROOT / record["image"])
            if box is None:
                continue
            box_height = float(box[3] - box[1])
            center_u = float(box[0] + box[2]) / 2.0
            bearing = math.atan((319.5 - center_u) / FOCAL_PX)
            raw_range = FOCAL_PX * 0.9 / box_height / math.cos(bearing)
            if math.isfinite(raw_range) and raw_range > 0.0:
                raw_ranges.append(raw_range)
                true_ranges.append(float(record["range_m"]))
    if len(raw_ranges) < 20:
        raise RuntimeError("insufficient validation detections for range calibration")
    scale, offset = np.polyfit(np.asarray(raw_ranges), np.asarray(true_ranges), 1)
    raw_errors = np.asarray(raw_ranges) - np.asarray(true_ranges)
    calibrated = scale * np.asarray(raw_ranges) + offset
    calibrated_errors = calibrated - np.asarray(true_ranges)
    return {
        "sample_count": len(raw_ranges),
        "range_scale": float(scale),
        "range_offset_m": float(offset),
        "raw_range_rmse_m": float(np.sqrt(np.mean(raw_errors ** 2))),
        "calibrated_range_rmse_m": float(np.sqrt(np.mean(calibrated_errors ** 2))),
        "source": "full-visible detections from yolo_val_mixed only",
    }


def main() -> None:
    manifest = json.loads(DATASET_MANIFEST.read_text(encoding="utf-8"))
    model = YOLO(str(STARTING_WEIGHTS))
    train_result = model.train(
        data=str(DATASET_YAML), epochs=50, patience=12, batch=4, imgsz=640,
        device=0, workers=1, amp=True, deterministic=True, seed=616,
        project=str(RUN_ROOT), name=RUN_NAME, exist_ok=False,
        pretrained=True, plots=True, verbose=True,
    )
    run_dir = Path(train_result.save_dir)
    best_path = run_dir / "weights" / "best.pt"
    TRAINED_WEIGHTS.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_path, TRAINED_WEIGHTS)
    trained_model = YOLO(str(TRAINED_WEIGHTS))
    test_result = trained_model.val(
        data=str(DATASET_YAML), split="test", imgsz=640, batch=4,
        device=0, plots=True, project=str(RUN_ROOT),
        name=f"{RUN_NAME}_test", exist_ok=False, verbose=True,
    )
    evidence = {
        "dataset_sha256": manifest["dataset_sha256"],
        "image_level_test": _image_level_test(trained_model),
        "status": "complete",
        "test_metrics": _jsonable(test_result.results_dict),
        "trained_checkpoint_path": str(TRAINED_WEIGHTS),
        "trained_checkpoint_sha256": _sha256(TRAINED_WEIGHTS),
        "trained_checkpoint_size_bytes": TRAINED_WEIGHTS.stat().st_size,
        "training_metrics": _jsonable(train_result.results_dict),
        "training_parameters": {
            "amp": True, "batch": 4, "deterministic": True,
            "device": 0, "epochs_max": 50, "image_size": 640,
            "patience": 12, "seed": 616, "workers": 1,
        },
        "ultralytics_version": ultralytics.__version__,
        "validation_range_calibration": _validation_calibration(trained_model),
    }
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_ROOT / "training_summary_v2.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
