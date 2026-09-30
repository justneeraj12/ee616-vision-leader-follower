#!/usr/bin/env python3
"""Compare raw YOLOv8n confidence across separated and failed domains."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from ultralytics import YOLO


WORKSPACE = Path("/workspace/work/ros2_ws")
MODEL_PATH = WORKSPACE / "models" / "yolov8n_predecessor_v2.pt"
V2_ROOT = WORKSPACE / "datasets" / "ee616_predecessor_target_v2"
FINAL_ROOT = WORKSPACE / "results" / "yolo_gate" / "v2_failure_diagnostics"
OUTPUT_PATH = WORKSPACE / "results" / "yolo_gate" / "domain_diagnosis_v2.json"
THRESHOLDS = (0.001, 0.01, 0.05, 0.10, 0.25)


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


def _analyze_domain(
    model: YOLO,
    root: Path,
    split: str,
    scene_prefix: str,
) -> dict[str, Any]:
    image_dir = root / "images" / split
    label_dir = root / "labels" / split
    images = sorted(image_dir.glob(f"{scene_prefix}_*.png"))
    records = []
    for image_path in images:
        label_box = _label_box(label_dir / f"{image_path.stem}.txt")
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
            confidence = None
            overlap = None
        else:
            confidences = result.boxes.conf.detach().cpu().numpy()
            best_index = int(np.argmax(confidences))
            confidence = float(confidences[best_index])
            prediction = result.boxes.xyxy[best_index].detach().cpu().numpy()
            overlap = _iou(prediction, label_box) if label_box else None
        records.append(
            {
                "confidence": confidence,
                "expected_positive": label_box is not None,
                "image": image_path.name,
                "iou_with_label": overlap,
            }
        )
    positives = [record for record in records if record["expected_positive"]]
    negatives = [record for record in records if not record["expected_positive"]]
    threshold_results = {}
    for threshold in THRESHOLDS:
        true_positive = sum(
            record["confidence"] is not None
            and record["confidence"] >= threshold
            and record["iou_with_label"] is not None
            and record["iou_with_label"] >= 0.5
            for record in positives
        )
        false_positive = sum(
            record["confidence"] is not None
            and record["confidence"] >= threshold
            for record in negatives
        )
        threshold_results[f"{threshold:.3f}"] = {
            "false_positive": false_positive,
            "positive_recall_iou_0_5": (
                true_positive / len(positives) if positives else None
            ),
            "true_positive_iou_0_5": true_positive,
        }
    positive_confidences = [
        record["confidence"]
        for record in positives
        if record["confidence"] is not None
    ]
    return {
        "image_count": len(records),
        "negative_label_count": len(negatives),
        "positive_confidence_max": (
            max(positive_confidences) if positive_confidences else None
        ),
        "positive_confidence_median": (
            float(np.median(positive_confidences))
            if positive_confidences
            else None
        ),
        "positive_label_count": len(positives),
        "records": records,
        "threshold_results": threshold_results,
    }


def main() -> None:
    model = YOLO(str(MODEL_PATH))
    domains = {
        "validation_yolo_val_mixed": (V2_ROOT, "val", "yolo_val_mixed"),
        "heldout_yolo_test_occlusion": (
            V2_ROOT,
            "test",
            "yolo_test_occlusion",
        ),
        "failed_camera_calibration": (
            FINAL_ROOT,
            "test",
            "camera_calibration",
        ),
        "failed_straight_aisle": (FINAL_ROOT, "test", "straight_aisle"),
    }
    evidence = {
        "domains": {
            name: _analyze_domain(model, *parameters)
            for name, parameters in domains.items()
        },
        "model_path": str(MODEL_PATH),
        "scope": (
            "Offline diagnosis of a failed gate. Failed final-scene images are "
            "excluded from training, calibration, and threshold selection."
        ),
        "status": "complete",
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
