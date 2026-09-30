"""Plot Gate 6 latency and resource evidence and write checksums."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt


def _resource_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_checksums(directory: Path) -> Path:
    paths = [
        *directory.glob("timing_*_samples.csv"),
        *directory.glob("timing_*_summary.json"),
        *directory.glob("disturbance_*_samples.csv"),
        *directory.glob("disturbance_*_summary.json"),
        directory / "resource_samples.csv",
        directory / "resources.json",
        directory / "summary.json",
        directory / "timing_gate_metrics.png",
    ]
    lines = []
    for path in sorted(set(paths), key=lambda item: item.name):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.name}")
    output = directory / "SHA256SUMS"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    summary = json.loads((args.directory / "summary.json").read_text(encoding="utf-8"))
    resource_rows = _resource_rows(args.directory / "resource_samples.csv")
    stages = [
        "camera_to_measurement",
        "measurement_to_controller_cmd",
        "controller_to_actual_cmd",
        "detector_inference",
        "control_period",
    ]
    labels = ["camera→measurement", "measurement→control", "control→actual", "inference", "control period"]
    figure, axes = plt.subplots(2, 1, figsize=(12, 8), constrained_layout=True)
    width = 0.24
    x_values = list(range(len(stages)))
    for index in range(1, 4):
        values = [summary["followers"][str(index)]["latency"][stage]["p95_ms_worst"] for stage in stages]
        axes[0].bar([x + (index - 2) * width for x in x_values], values, width=width, label=f"Follower {index}")
    axes[0].axhline(66.7, color="tab:red", linestyle="--", label="66.7 ms limit")
    axes[0].set_xticks(x_values, labels, rotation=15, ha="right")
    axes[0].set(title="Worst p95 latency across three combined runs", ylabel="Latency (ms)")
    axes[0].grid(axis="y", alpha=0.3)
    axes[0].legend(fontsize=8)
    elapsed = [float(row["elapsed_s"]) for row in resource_rows]
    memory = [float(row["memory_mib"]) for row in resource_rows]
    gpu_memory = [float(row["gpu_memory_mib"]) for row in resource_rows]
    cpu = [float(row["cpu_core_equivalent_percent"]) for row in resource_rows]
    axes[1].plot(elapsed, memory, label="Container RAM (MiB)")
    axes[1].plot(elapsed, gpu_memory, label="GPU memory (MiB)")
    axes[1].set(title="Resource time series for the three-run window", xlabel="Elapsed wall time (s)", ylabel="Memory (MiB)")
    axes[1].grid(alpha=0.3)
    resource_axis = axes[1].twinx()
    resource_axis.plot(elapsed, cpu, color="tab:green", alpha=0.55, label="CPU core-equivalent (%)")
    resource_axis.set_ylabel("CPU core-equivalent (%)")
    handles, labels_left = axes[1].get_legend_handles_labels()
    handles_right, labels_right = resource_axis.get_legend_handles_labels()
    axes[1].legend(handles + handles_right, labels_left + labels_right, fontsize=8, loc="upper right")
    figure.suptitle("EE 616 target-laptop timing and resource evidence")
    output = args.directory / "timing_gate_metrics.png"
    figure.savefig(output, dpi=180)
    plt.close(figure)
    print(output)
    print(_write_checksums(args.directory))


if __name__ == "__main__":
    main()
