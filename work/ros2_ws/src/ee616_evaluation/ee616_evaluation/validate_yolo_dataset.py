"""Validate YOLO image-label pairs and write a reproducibility manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_dataset(root: Path) -> dict[str, Any]:
    """Validate three split directories and return a manifest."""
    root = root.resolve()
    manifest: dict[str, Any] = {
        "dataset_id": root.name,
        "format": "Ultralytics YOLO normalized xywh",
        "scope": "detector training data; not detector performance evidence",
        "splits": {},
    }
    dataset_digest = hashlib.sha256()
    split_image_hashes: dict[str, set[str]] = {}
    for split in ("train", "val", "test"):
        images_dir = root / "images" / split
        labels_dir = root / "labels" / split
        image_paths = sorted(images_dir.glob("*.png"))
        if not image_paths:
            raise ValueError(f"{split} contains no PNG images")
        positives = 0
        negatives = 0
        image_hashes: set[str] = set()
        split_digest = hashlib.sha256()
        for image_path in image_paths:
            label_path = labels_dir / f"{image_path.stem}.txt"
            if not label_path.is_file():
                raise ValueError(f"missing label for {image_path.name}")
            label_text = label_path.read_text(encoding="utf-8").strip()
            if label_text:
                positives += 1
                fields = label_text.split()
                if len(fields) != 5 or fields[0] != "0":
                    raise ValueError(f"invalid label format in {label_path}")
                values = [float(value) for value in fields[1:]]
                if any(value < 0.0 or value > 1.0 for value in values):
                    raise ValueError(f"out-of-range label in {label_path}")
                if values[2] <= 0.0 or values[3] <= 0.0:
                    raise ValueError(f"non-positive box in {label_path}")
            else:
                negatives += 1
            for path in (image_path, label_path):
                relative = path.relative_to(root).as_posix()
                file_hash = _sha256(path)
                dataset_digest.update(relative.encode("utf-8"))
                dataset_digest.update(file_hash.encode("ascii"))
                split_digest.update(relative.encode("utf-8"))
                split_digest.update(file_hash.encode("ascii"))
                if path == image_path:
                    image_hashes.add(file_hash)
        extra_labels = {
            path.stem for path in labels_dir.glob("*.txt")
        } - {path.stem for path in image_paths}
        if extra_labels:
            raise ValueError(f"orphan labels in {split}: {sorted(extra_labels)}")
        manifest["splits"][split] = {
            "images": len(image_paths),
            "negative_labels": negatives,
            "positive_labels": positives,
            "sha256": split_digest.hexdigest(),
            "unique_images": len(image_hashes),
        }
        split_image_hashes[split] = image_hashes
    overlaps = {
        "train_test": len(
            split_image_hashes["train"] & split_image_hashes["test"]
        ),
        "train_val": len(
            split_image_hashes["train"] & split_image_hashes["val"]
        ),
        "val_test": len(
            split_image_hashes["val"] & split_image_hashes["test"]
        ),
    }
    if any(overlaps.values()):
        raise ValueError(f"identical images cross dataset splits: {overlaps}")
    manifest["cross_split_duplicate_images"] = overlaps
    manifest["dataset_sha256"] = dataset_digest.hexdigest()
    manifest["status"] = "pass"
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate_dataset(args.dataset_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    counts = {
        split: values["images"] for split, values in result["splits"].items()
    }
    print(json.dumps({"dataset_sha256": result["dataset_sha256"], **counts}))


if __name__ == "__main__":
    main()
