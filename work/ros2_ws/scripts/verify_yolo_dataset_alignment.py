#!/usr/bin/env python3
"""Verify that YOLO labels overlap the rendered red target in every image."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median
from typing import Any

import cv2
import numpy as np


def _label_box(path: Path, width: int, height: int) -> tuple[int, int, int, int] | None:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return None
    fields = text.split()
    if len(fields) != 5 or fields[0] != "0":
        raise ValueError(f"invalid label format in {path}")
    center_x, center_y, box_width, box_height = map(float, fields[1:])
    return (
        round((center_x - box_width / 2.0) * width),
        round((center_y - box_height / 2.0) * height),
        round((center_x + box_width / 2.0) * width),
        round((center_y + box_height / 2.0) * height),
    )


def _iou(first: tuple[int, int, int, int], second: tuple[int, int, int, int]) -> float:
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[2], second[2])
    bottom = min(first[3], second[3])
    intersection = max(0, right - left) * max(0, bottom - top)
    first_area = max(0, first[2] - first[0]) * max(0, first[3] - first[1])
    second_area = max(0, second[2] - second[0]) * max(0, second[3] - second[1])
    union = first_area + second_area - intersection
    return intersection / union if union else 0.0


def _target_mask(image: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    low_red = cv2.inRange(hsv, np.array([0, 150, 30]), np.array([12, 255, 255]))
    high_red = cv2.inRange(hsv, np.array([170, 150, 30]), np.array([179, 255, 255]))
    return cv2.bitwise_or(low_red, high_red)


def _target_components(mask: np.ndarray) -> list[tuple[int, int, int, int]]:
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    boxes = []
    for index in range(1, count):
        x, y, width, height, area = stats[index]
        if area >= 20 and width >= 2 and height >= 2:
            boxes.append((int(x), int(y), int(x + width), int(y + height)))
    return boxes


def verify(root: Path, minimum_visible_pixels: int) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for split in ("train", "val", "test"):
        for image_path in sorted((root / "images" / split).glob("*.png")):
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"unable to read {image_path}")
            height, width = image.shape[:2]
            label_path = root / "labels" / split / f"{image_path.stem}.txt"
            label = _label_box(label_path, width, height)
            mask = _target_mask(image)
            components = _target_components(mask)
            overlap = None
            visible_pixels = 0
            if label is not None:
                overlap = max((_iou(label, box) for box in components), default=0.0)
                left, top, right, bottom = label
                visible_pixels = int(np.count_nonzero(mask[top:bottom, left:right]))
            records.append(
                {
                    "image": image_path.relative_to(root).as_posix(),
                    "label_positive": label is not None,
                    "red_components": len(components),
                    "maximum_iou": overlap,
                    "visible_component_box_pixels_inside_label": visible_pixels,
                }
            )

    positives = [record for record in records if record["label_positive"]]
    overlaps = [float(record["maximum_iou"]) for record in positives]
    failures = [
        record
        for record in positives
        if record["visible_component_box_pixels_inside_label"]
        < minimum_visible_pixels
    ]
    negative_failures = [
        record
        for record in records
        if not record["label_positive"] and record["red_components"] > 0
    ]
    result = {
        "dataset_id": root.name,
        "method": "HSV red-target connected components compared with YOLO labels",
        "minimum_visible_component_box_pixels_required": minimum_visible_pixels,
        "images_checked": len(records),
        "positive_labels_checked": len(positives),
        "minimum_iou_observed": min(overlaps) if overlaps else None,
        "median_iou_observed": median(overlaps) if overlaps else None,
        "failed_positive_labels": len(failures),
        "negative_labels_with_visible_red_component": len(negative_failures),
        "failures": failures + negative_failures,
        "status": (
            "pass" if overlaps and not failures and not negative_failures else "fail"
        ),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum-visible-pixels", type=int, default=20)
    args = parser.parse_args()
    result = verify(args.dataset_root.resolve(), args.minimum_visible_pixels)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in result.items() if key != "failures"}))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
