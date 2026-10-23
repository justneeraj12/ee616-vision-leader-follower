"""Create poster-ready plots from the warehouse mission evidence."""

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
    labels = ["F1", "F2", "F3"]
    means = [
        summary["chains"]["3"]["followers"][str(index)][
            "transport_spacing_rmse_m_mean"
        ]
        for index in (1, 2, 3)
    ]
    trace_path = args.directory / "warehouse_mission_3_run_03_samples.csv"
    with trace_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    figure, axes = plt.subplots(1, 2, figsize=(11.5, 4.5), constrained_layout=True)
    axes[0].bar(labels, means, color=["#1677b8", "#2d9c67", "#e58b2a"])
    axes[0].axhline(0.20, color="black", linestyle="--", label="F1 criterion")
    axes[0].axhline(0.25, color="#b52d31", linestyle=":", label="rear criterion")
    axes[0].set(
        title="Transport spacing error across three runs",
        ylabel="Spacing RMSE (m)",
    )
    axes[0].grid(axis="y", alpha=0.25)
    axes[0].legend(fontsize=8)
    for index, color in zip((1, 2, 3), ("#1677b8", "#2d9c67", "#e58b2a")):
        selected = [row for row in rows if int(row["follower_index"]) == index]
        axes[1].plot(
            [float(row["elapsed_s"]) for row in selected],
            [float(row["true_range_m"]) for row in selected],
            color=color,
            label=f"Follower {index}",
        )
    axes[1].axhline(1.5, color="black", linestyle="--", label="Desired range")
    axes[1].set(
        title="Full pickup-to-drop-off mission, run 03",
        xlabel="Simulation time (s)",
        ylabel="Camera-to-target range (m)",
    )
    axes[1].grid(alpha=0.25)
    axes[1].legend(fontsize=8)
    figure.suptitle("EE 616 warehouse convoy mission evidence")
    output = args.directory / "warehouse_mission_metrics.png"
    figure.savefig(output, dpi=200)
    plt.close(figure)
    print(output)


if __name__ == "__main__":
    main()
