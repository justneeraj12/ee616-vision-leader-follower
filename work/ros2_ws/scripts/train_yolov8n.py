#!/usr/bin/env python3
"""Train the frozen YOLOv8n target experiment and retain compact evidence."""

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
TRAINED_WEIGHTS = WORKSPACE / "models" / "yolov8n_predecessor_v1.pt"
DATASET_YAML = WORKSPACE / "experiments" / "yolov8n_gate" / "dataset.yaml"
DATASET_ROOT = WORKSPACE / "datasets" / "ee616_predecessor_target_v1"
RUN_ROOT = WORKSPACE / "results" / "yolo_training"
RUN_NAME = "run_20260929_v2"
ATTEMPT_ID = "attempt_2"
EVIDENCE_ROOT = WORKSPACE / "results" / "yolo_gate"


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


def _image_level_test(model: YOLO) -> dict[str, Any]:
    images = sorted((DATASET_ROOT / "images" / "test").glob("*.png"))
    counts = {"true_positive": 0, "true_negative": 0, "false_positive": 0, "false_negative": 0}
    latencies = []
    model.predict(
        source=np.zeros((480, 640, 3), dtype=np.uint8),
        imgsz=640,
        conf=0.25,
        iou=0.45,
        device=0,
        verbose=False,
    )
    for image_path in images:
        label_path = DATASET_ROOT / "labels" / "test" / f"{image_path.stem}.txt"
        expected = bool(label_path.read_text(encoding="utf-8").strip())
        started = perf_counter()
        result = model.predict(
            source=str(image_path),
            imgsz=640,
            conf=0.25,
            iou=0.45,
            classes=[0],
            device=0,
            verbose=False,
        )[0]
        latencies.append((perf_counter() - started) * 1000.0)
        predicted = result.boxes is not None and len(result.boxes) > 0
        if expected and predicted:
            counts["true_positive"] += 1
        elif expected:
            counts["false_negative"] += 1
        elif predicted:
            counts["false_positive"] += 1
        else:
            counts["true_negative"] += 1
    latencies.sort()
    p95_index = max(0, math.ceil(0.95 * len(latencies)) - 1)
    positives = counts["true_positive"] + counts["false_negative"]
    negatives = counts["true_negative"] + counts["false_positive"]
    return {
        **counts,
        "false_negative_rate": counts["false_negative"] / positives,
        "false_positive_rate": counts["false_positive"] / negatives,
        "image_count": len(images),
        "latency_median_ms": float(np.median(latencies)),
        "latency_p95_ms": latencies[p95_index],
        "scope": "held-out dataset test split; not the A012 measurement gate",
    }


def main() -> None:
    if not STARTING_WEIGHTS.is_file():
        raise FileNotFoundError(f"missing starting weights: {STARTING_WEIGHTS}")
    if not DATASET_YAML.is_file():
        raise FileNotFoundError(f"missing dataset config: {DATASET_YAML}")
    model = YOLO(str(STARTING_WEIGHTS))
    train_result = model.train(
        data=str(DATASET_YAML),
        epochs=40,
        patience=10,
        batch=4,
        imgsz=640,
        device=0,
        workers=1,
        amp=True,
        deterministic=True,
        seed=616,
        project=str(RUN_ROOT),
        name=RUN_NAME,
        exist_ok=False,
        pretrained=True,
        plots=True,
        verbose=True,
    )
    run_dir = Path(train_result.save_dir)
    best_path = run_dir / "weights" / "best.pt"
    if not best_path.is_file():
        raise FileNotFoundError(f"training did not produce {best_path}")
    TRAINED_WEIGHTS.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_path, TRAINED_WEIGHTS)
    trained_model = YOLO(str(TRAINED_WEIGHTS))
    test_result = trained_model.val(
        data=str(DATASET_YAML),
        split="test",
        imgsz=640,
        batch=4,
        device=0,
        plots=True,
        project=str(RUN_ROOT),
        name=f"{RUN_NAME}_test",
        exist_ok=False,
        verbose=True,
    )
    image_test = _image_level_test(trained_model)
    evidence = {
        "dataset_sha256": "1049c1491947995b3439d482c6f2bcc86425d52d31d05cc9b43ba92be9e6579a",
        "attempt_id": ATTEMPT_ID,
        "image_level_test": image_test,
        "scope": "YOLO training and held-out dataset test; not A012 measurement-gate evidence",
        "starting_checkpoint_sha256": _sha256(STARTING_WEIGHTS),
        "status": "complete",
        "test_metrics": _jsonable(test_result.results_dict),
        "trained_checkpoint_path": str(TRAINED_WEIGHTS),
        "trained_checkpoint_sha256": _sha256(TRAINED_WEIGHTS),
        "trained_checkpoint_size_bytes": TRAINED_WEIGHTS.stat().st_size,
        "training_metrics": _jsonable(train_result.results_dict),
        "training_parameters": {
            "amp": True,
            "batch": 4,
            "deterministic": True,
            "device": 0,
            "epochs_max": 40,
            "image_size": 640,
            "patience": 10,
            "seed": 616,
            "workers": 1,
        },
        "ultralytics_version": ultralytics.__version__,
    }
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_ROOT / "training_summary.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
