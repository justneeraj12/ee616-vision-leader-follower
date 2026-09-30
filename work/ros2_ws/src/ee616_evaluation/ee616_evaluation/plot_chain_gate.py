"""Create traceable plots from the incremental-chain evidence."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    summary = json.loads((args.directory / "summary.json").read_text(encoding="utf-8"))
    labels, means = [], []
    for count in (2, 3):
        for index in range(1, count + 1):
            labels.append(f"{count}-follower\nF{index}")
            means.append(summary["chains"][str(count)]["followers"][str(index)]["spacing_rmse_m_mean"])
    trace_path = args.directory / "chain_3_turn_run_03_samples.csv"
    with trace_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)
    axes[0].bar(labels, means, color="tab:blue")
    axes[0].axhline(0.20, color="black", linestyle="--", label="F1 limit")
    axes[0].axhline(0.25, color="tab:red", linestyle=":", label="Rear-follower limit")
    axes[0].set(title="Mean spacing RMSE across six nominal runs", ylabel="RMSE (m)")
    axes[0].grid(axis="y", alpha=0.3)
    axes[0].legend(fontsize=8)
    for index in (1, 2, 3):
        selected = [row for row in rows if int(row["follower_index"]) == index]
        axes[1].plot(
            [float(row["elapsed_s"]) for row in selected],
            [float(row["true_range_m"]) for row in selected],
            label=f"Follower {index}",
        )
    axes[1].axhline(1.5, color="black", linestyle="--", label="Desired range")
    axes[1].set(title="Three-follower gradual turn, run 03", xlabel="Elapsed time (s)", ylabel="Range (m)")
    axes[1].grid(alpha=0.3)
    axes[1].legend(fontsize=8)
    figure.suptitle("EE 616 nominal incremental-chain Gazebo evidence")
    output = args.directory / "chain_gate_metrics.png"
    figure.savefig(output, dpi=180)
    plt.close(figure)
    print(output)


if __name__ == "__main__":
    main()
