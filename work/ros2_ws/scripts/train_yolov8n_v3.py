#!/usr/bin/env python3
"""Train synchronized YOLOv8n v3 with validation-only parameter selection."""

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
TRAINED_WEIGHTS = WORKSPACE / "models" / "yolov8n_predecessor_v3.pt"
DATASET_YAML = WORKSPACE / "experiments" / "yolov8n_gate" / "dataset_v3.yaml"
DATASET_ROOT = WORKSPACE / "datasets" / "ee616_predecessor_target_v3"
DATASET_MANIFEST = WORKSPACE / "results" / "yolo_dataset" / "dataset_v3_manifest.json"
RUN_ROOT = WORKSPACE / "results" / "yolo_training"
RUN_NAME = "run_20260929_synchronized_v3"
EVIDENCE_ROOT = WORKSPACE / "results" / "yolo_gate"
FOCAL_PX = 640.0 / (2.0 * math.tan(1.2217304764 / 2.0))
THRESHOLDS = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40)


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


def _label_box(path: Path) -> tuple[float, float, float, float] | None:
    fields = path.read_text(encoding="utf-8").split()
    if len(fields) != 5:
        return None
    center_x, center_y, width, height = (float(value) for value in fields[1:])
    return (
        (center_x - width / 2.0) * 640.0,
        (center_y - height / 2.0) * 480.0,
        (center_x + width / 2.0) * 640.0,
        (center_y + height / 2.0) * 480.0,
    )


def _iou(first: np.ndarray, second: tuple[float, ...]) -> float:
    x_min = max(float(first[0]), second[0])
    y_min = max(float(first[1]), second[1])
    x_max = min(float(first[2]), second[2])
    y_max = min(float(first[3]), second[3])
    intersection = max(0.0, x_max - x_min) * max(0.0, y_max - y_min)
    first_area = max(0.0, float(first[2] - first[0]))
    first_area *= max(0.0, float(first[3] - first[1]))
    second_area = max(0.0, second[2] - second[0])
    second_area *= max(0.0, second[3] - second[1])
    union = first_area + second_area - intersection
    return intersection / union if union > 0.0 else 0.0


def _best_raw_prediction(model: YOLO, image_path: Path) -> dict[str, Any]:
    result = model.predict(
        source=str(image_path),
        imgsz=640,
        conf=0.001,
        iou=0.45,
        classes=[0],
        device=0,
        verbose=False,
    )[0]
    if result.boxes is None or len(result.boxes) == 0:
        return {"box": None, "confidence": None}
    confidences = result.boxes.conf.detach().cpu().numpy()
    index = int(np.argmax(confidences))
    return {
        "box": result.boxes.xyxy[index].detach().cpu().numpy(),
        "confidence": float(confidences[index]),
    }


def _prediction_records(model: YOLO, split: str) -> list[dict[str, Any]]:
    records = []
    for image_path in sorted((DATASET_ROOT / "images" / split).glob("*.png")):
        label_path = DATASET_ROOT / "labels" / split / f"{image_path.stem}.txt"
        label_box = _label_box(label_path)
        started = perf_counter()
        prediction = _best_raw_prediction(model, image_path)
        latency_ms = (perf_counter() - started) * 1000.0
        overlap = (
            _iou(prediction["box"], label_box)
            if prediction["box"] is not None and label_box is not None
            else None
        )
        records.append(
            {
                "box": prediction["box"],
                "confidence": prediction["confidence"],
                "expected_positive": label_box is not None,
                "image_path": image_path,
                "iou": overlap,
                "label_box": label_box,
                "latency_ms": latency_ms,
            }
        )
    return records


def _score(records: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    positive_count = sum(record["expected_positive"] for record in records)
    true_positive = 0
    mislocalized = 0
    false_positive = 0
    true_negative = 0
    missed = 0
    for record in records:
        detected = (
            record["confidence"] is not None
            and record["confidence"] >= threshold
        )
        if record["expected_positive"]:
            if not detected:
                missed += 1
            elif record["iou"] is not None and record["iou"] >= 0.5:
                true_positive += 1
            else:
                mislocalized += 1
        elif detected:
            false_positive += 1
        else:
            true_negative += 1
    precision_denominator = true_positive + mislocalized + false_positive
    precision = (
        true_positive / precision_denominator
        if precision_denominator
        else 0.0
    )
    recall = true_positive / positive_count if positive_count else 0.0
    f1 = (
        2.0 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    latencies = sorted(float(record["latency_ms"]) for record in records)
    p95_index = max(0, math.ceil(0.95 * len(latencies)) - 1)
    return {
        "f1_iou_0_5": f1,
        "false_positive": false_positive,
        "image_count": len(records),
        "latency_median_ms": float(np.median(latencies)),
        "latency_p95_ms": latencies[p95_index],
        "mislocalized_positive": mislocalized,
        "missed_positive": missed,
        "precision_iou_0_5": precision,
        "recall_iou_0_5": recall,
        "threshold": threshold,
        "true_negative": true_negative,
        "true_positive_iou_0_5": true_positive,
    }


def _select_threshold(records: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [_score(records, threshold) for threshold in THRESHOLDS]
    selected = max(
        candidates,
        key=lambda item: (
            item["f1_iou_0_5"],
            item["precision_iou_0_5"],
            item["threshold"],
        ),
    )
    return {"candidates": candidates, "selected": selected}


def _validation_calibration(
    records: list[dict[str, Any]],
    threshold: float,
) -> dict[str, Any]:
    metadata_path = DATASET_ROOT / "metadata" / "val_yolo_val_v3.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    ranges_by_name = {
        Path(record["image"]).name: float(record["range_m"])
        for record in metadata["records"]
    }
    raw_ranges = []
    true_ranges = []
    for record in records:
        label = record["label_box"]
        box = record["box"]
        if label is None or box is None:
            continue
        if record["confidence"] < threshold or record["iou"] < 0.5:
            continue
        if label[0] <= 3.2 or label[1] <= 2.4:
            continue
        if label[2] >= 636.8 or label[3] >= 477.6:
            continue
        box_height = float(box[3] - box[1])
        center_u = float(box[0] + box[2]) / 2.0
        bearing = math.atan((319.5 - center_u) / FOCAL_PX)
        raw_range = FOCAL_PX * 0.9 / box_height / math.cos(bearing)
        if math.isfinite(raw_range) and raw_range > 0.0:
            raw_ranges.append(raw_range)
            true_ranges.append(ranges_by_name[record["image_path"].name])
    if len(raw_ranges) < 20:
        raise RuntimeError("insufficient correct validation boxes for calibration")
    raw_array = np.asarray(raw_ranges)
    true_array = np.asarray(true_ranges)
    scale, offset = np.polyfit(raw_array, true_array, 1)
    calibrated = scale * raw_array + offset
    return {
        "calibrated_range_rmse_m": float(
            np.sqrt(np.mean((calibrated - true_array) ** 2))
        ),
        "range_offset_m": float(offset),
        "range_scale": float(scale),
        "raw_range_rmse_m": float(
            np.sqrt(np.mean((raw_array - true_array) ** 2))
        ),
        "sample_count": len(raw_ranges),
        "source": "correctly localized full-visible yolo_val_v3 boxes only",
    }


def main() -> None:
    manifest = json.loads(DATASET_MANIFEST.read_text(encoding="utf-8"))
    model = YOLO(str(STARTING_WEIGHTS))
    train_result = model.train(
        data=str(DATASET_YAML),
        epochs=50,
        patience=12,
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
    TRAINED_WEIGHTS.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_path, TRAINED_WEIGHTS)
    trained_model = YOLO(str(TRAINED_WEIGHTS))
    validation_records = _prediction_records(trained_model, "val")
    threshold_selection = _select_threshold(validation_records)
    threshold = float(threshold_selection["selected"]["threshold"])
    test_records = _prediction_records(trained_model, "test")
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
    evidence = {
        "dataset_sha256": manifest["dataset_sha256"],
        "status": "complete",
        "test_image_level": _score(test_records, threshold),
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
            "epochs_max": 50,
            "image_size": 640,
            "patience": 12,
            "seed": 616,
            "workers": 1,
        },
        "ultralytics_version": ultralytics.__version__,
        "validation_range_calibration": _validation_calibration(
            validation_records,
            threshold,
        ),
        "validation_threshold_selection": threshold_selection,
    }
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_ROOT / "training_summary_v3.json").write_text(
        json.dumps(_jsonable(evidence), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(_jsonable(evidence), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
