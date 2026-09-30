"""Plot controlled-disturbance results from retained raw rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt


def _rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_checksums(directory: Path) -> Path:
    names = [
        *directory.glob("disturbance_*_samples.csv"),
        *directory.glob("disturbance_*_summary.json"),
        directory / "pair_stage_summary.json",
        directory / "resources.json",
        directory / "summary.json",
        directory / "disturbance_gate_metrics.png",
    ]
    lines = []
    for path in sorted(set(names), key=lambda item: item.name):
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
    labels, values = [], []
    for key, group in summary["groups"].items():
        count, scenario = key.split("_", 1)
        for index, metrics in group["followers"].items():
            labels.append(f"{scenario.replace('_', ' ')}\n{count}F-F{index}")
            values.append(metrics["spacing_rmse_m_worst"])
    long_rows = _rows(args.directory / "disturbance_1_long_occlusion_run_03_samples.csv")
    long_rows = [row for row in long_rows if int(row["follower_index"]) == 1]
    state_value = {"SAFE_STOP": 0, "PREDICT": 1, "TRACK": 2, "UNSEEN": -1}
    figure, axes = plt.subplots(2, 1, figsize=(12, 8), constrained_layout=True)
    axes[0].bar(range(len(values)), values, color="tab:blue")
    axes[0].axhline(0.30, color="black", linestyle="--", label="F1 disturbed-RMSE limit")
    axes[0].axhline(0.35, color="tab:red", linestyle=":", label="Rear-follower limit")
    axes[0].set_xticks(range(len(labels)), labels, rotation=25, ha="right", fontsize=8)
    axes[0].set(title="Worst spacing RMSE across repeated disturbance runs", ylabel="RMSE (m)")
    axes[0].grid(axis="y", alpha=0.3)
    axes[0].legend(fontsize=8)
    times = [float(row["elapsed_s"]) for row in long_rows]
    axes[1].step(times, [state_value.get(row["control_state"], -1) for row in long_rows], where="post", label="Supervisor state")
    event_times = [float(row["elapsed_s"]) for row in long_rows if row["event"] == "LONG_OCCLUSION"]
    if event_times:
        axes[1].axvspan(min(event_times), max(event_times), color="tab:orange", alpha=0.25, label="Camera blackout")
    axes[1].set_yticks([0, 1, 2], ["SAFE STOP", "PREDICT", "TRACK"])
    axes[1].set(title="Long-occlusion state response, pair run 03", xlabel="Elapsed time (s)")
    axes[1].grid(alpha=0.3)
    axes[1].legend(fontsize=8)
    figure.suptitle("EE 616 controlled-disturbance Gazebo evidence")
    output = args.directory / "disturbance_gate_metrics.png"
    figure.savefig(output, dpi=180)
    plt.close(figure)
    print(output)
    print(_write_checksums(args.directory))


if __name__ == "__main__":
    main()
