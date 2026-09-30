#!/usr/bin/env python3
"""Remove projected labels when the rendered target is fully occluded."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np


def _target_mask(image: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    low_red = cv2.inRange(hsv, np.array([0, 150, 30]), np.array([12, 255, 255]))
    high_red = cv2.inRange(hsv, np.array([170, 150, 30]), np.array([179, 255, 255]))
    return cv2.bitwise_or(low_red, high_red)


def _label_bounds(text: str, width: int, height: int) -> tuple[int, int, int, int]:
    fields = text.split()
    if len(fields) != 5 or fields[0] != "0":
        raise ValueError("expected one class-zero YOLO label")
    center_x, center_y, box_width, box_height = map(float, fields[1:])
    return (
        max(0, round((center_x - box_width / 2.0) * width)),
        max(0, round((center_y - box_height / 2.0) * height)),
        min(width, round((center_x + box_width / 2.0) * width)),
        min(height, round((center_y + box_height / 2.0) * height)),
    )


def filter_labels(root: Path, minimum_visible_pixels: int, apply: bool) -> dict[str, Any]:
    positive_labels_entering_filter = 0
    removed_this_pass: list[str] = []
    for split in ("train", "val", "test"):
        for image_path in sorted((root / "images" / split).glob("*.png")):
            label_path = root / "labels" / split / f"{image_path.stem}.txt"
            label_text = label_path.read_text(encoding="utf-8").strip()
            if not label_text:
                continue
            positive_labels_entering_filter += 1
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"unable to read {image_path}")
            height, width = image.shape[:2]
            left, top, right, bottom = _label_bounds(label_text, width, height)
            visible_pixels = int(
                np.count_nonzero(_target_mask(image)[top:bottom, left:right])
            )
            if visible_pixels >= minimum_visible_pixels:
                continue
            relative_label = label_path.relative_to(root).as_posix()
            removed_this_pass.append(relative_label)
            if apply:
                label_path.write_text("", encoding="utf-8")

    projected_positives = 0
    retained_positives = 0
    removed: list[str] = []
    for metadata_path in sorted((root / "metadata").glob("*.json")):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        for record in metadata.get("records", []):
            if not record.get("positive_label"):
                continue
            projected_positives += 1
            label_path = root / record["label"]
            if label_path.read_text(encoding="utf-8").strip():
                retained_positives += 1
            else:
                removed.append(record["label"])

    return {
        "dataset_id": root.name,
        "method": "evaluation-only projection followed by rendered-target visibility filter",
        "minimum_visible_target_pixels": minimum_visible_pixels,
        "positive_labels_entering_filter": positive_labels_entering_filter,
        "removed_labels_this_pass": len(removed_this_pass),
        "projected_positive_labels": projected_positives,
        "retained_positive_labels": retained_positives,
        "removed_fully_occluded_or_unrendered_labels": len(removed),
        "removed_labels": removed,
        "applied": apply,
        "status": "pass",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum-visible-pixels", type=int, default=20)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    result = filter_labels(
        args.dataset_root.resolve(), args.minimum_visible_pixels, args.apply
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in result.items() if key != "removed_labels"}))


if __name__ == "__main__":
    main()
