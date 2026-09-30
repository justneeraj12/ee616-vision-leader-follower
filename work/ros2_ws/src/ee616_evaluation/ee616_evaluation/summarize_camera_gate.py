"""Combine camera-gate scene CSV files and create compact figures."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from ee616_evaluation.metrics import summarize_rows

import matplotlib.pyplot as plt

plt.switch_backend("Agg")


def _as_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def read_rows(paths: list[Path]) -> list[dict]:
    """Read evaluator CSV files with metric fields converted to numbers."""
    rows = []
    for path in paths:
        with path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                row["valid"] = _as_bool(row["valid"])
                row["full_visibility"] = _as_bool(row["full_visibility"])
                for key in (
                    "actual_range_m",
                    "actual_bearing_deg",
                    "measured_range_m",
                    "measured_bearing_deg",
                    "range_error_m",
                    "bearing_error_deg",
                    "inference_ms",
                    "detection_confidence",
                    "bbox_x",
                    "bbox_y",
                    "bbox_width",
                    "bbox_height",
                ):
                    value = row.get(key)
                    row[key] = float(value) if value else None
                rows.append(row)
    return rows


def write_figures(rows: list[dict], output_dir: Path) -> None:
    """Write error scatter plots for valid full-visibility samples."""
    valid = [
        row for row in rows if row["valid"] and row["full_visibility"]
    ]
    scenes = sorted({row["scene"] for row in valid})
    fig, axes = plt.subplots(2, 1, figsize=(8, 7), constrained_layout=True)
    for scene in scenes:
        selected = [row for row in valid if row["scene"] == scene]
        axes[0].scatter(
            [row["actual_range_m"] for row in selected],
            [row["range_error_m"] for row in selected],
            s=9,
            alpha=0.55,
            label=scene,
        )
        axes[1].scatter(
            [row["actual_bearing_deg"] for row in selected],
            [row["bearing_error_deg"] for row in selected],
            s=9,
            alpha=0.55,
            label=scene,
        )
    axes[0].axhline(0.0, color="black", linewidth=0.8)
    axes[0].set_xlabel("Gazebo ground-truth range (m)")
    axes[0].set_ylabel("Range error (m)")
    axes[0].legend()
    axes[1].axhline(0.0, color="black", linewidth=0.8)
    axes[1].set_xlabel("Gazebo ground-truth bearing (deg)")
    axes[1].set_ylabel("Bearing error (deg)")
    axes[1].legend()
    fig.suptitle("Camera-only fixed-target measurement errors")
    fig.savefig(output_dir / "camera_measurement_errors.png", dpi=160)
    plt.close(fig)


def main(args=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/camera_measurement_gate"),
    )
    parser.add_argument("--require-latency", action="store_true")
    parser.add_argument(
        "--scope",
        default="camera-only fixed-red-target baseline in Gazebo",
    )
    parsed = parser.parse_args(args)
    paths = sorted(parsed.output_dir.glob("*_samples.csv"))
    if not paths:
        parser.error(f"No scene CSV files found in {parsed.output_dir}")
    rows = read_rows(paths)
    summary = summarize_rows(rows, require_latency=parsed.require_latency)
    summary.update(
        {
            "scenes": sorted({row["scene"] for row in rows}),
            "source_csv_files": [path.name for path in paths],
            "ground_truth_boundary": (
                "Gazebo pose data is read only by ee616_evaluation and is "
                "not published to perception, estimation, supervision, or control."
            ),
            "scope": parsed.scope,
        }
    )
    (parsed.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_figures(rows, parsed.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if summary["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
