"""Create a traceable summary figure from raw pair-gate CSV evidence."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


def _rows(path: Path) -> list[dict[str, float | str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [
            {
                **row,
                "elapsed_s": float(row["elapsed_s"]),
                "true_range_m": float(row["true_range_m"]),
                "true_bearing_deg": float(row["true_bearing_deg"]),
                "follower_linear_cmd_mps": float(row["follower_linear_cmd_mps"]),
            }
            for row in csv.DictReader(handle)
        ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    straight = _rows(args.directory / "straight_run_03_samples.csv")
    turn = _rows(args.directory / "turn_run_03_samples.csv")
    figure, axes = plt.subplots(2, 2, figsize=(10, 6), constrained_layout=True)
    for rows, label, axis in (
        (straight, "Straight run 03", axes[0, 0]),
        (turn, "Turn run 03", axes[0, 1]),
    ):
        axis.plot([row["elapsed_s"] for row in rows], [row["true_range_m"] for row in rows], label="True camera-target range")
        axis.axhline(1.5, color="black", linestyle="--", label="Desired range")
        axis.set(title=label, xlabel="Elapsed time (s)", ylabel="Range (m)")
        axis.grid(alpha=0.3)
        axis.legend(fontsize=8)
    axes[1, 0].plot(
        [row["elapsed_s"] for row in turn],
        [row["true_bearing_deg"] for row in turn],
        color="tab:orange",
    )
    axes[1, 0].set(title="Gradual-turn bearing", xlabel="Elapsed time (s)", ylabel="Bearing (deg)")
    axes[1, 0].grid(alpha=0.3)
    axes[1, 1].plot(
        [row["elapsed_s"] for row in turn],
        [row["follower_linear_cmd_mps"] for row in turn],
        color="tab:green",
    )
    axes[1, 1].set(title="Follower linear command", xlabel="Elapsed time (s)", ylabel="Command (m/s)")
    axes[1, 1].grid(alpha=0.3)
    figure.suptitle("EE 616 one-pair nominal Gazebo evidence")
    output = args.directory / "pair_gate_metrics.png"
    figure.savefig(output, dpi=180)
    plt.close(figure)
    print(output)


if __name__ == "__main__":
    main()
