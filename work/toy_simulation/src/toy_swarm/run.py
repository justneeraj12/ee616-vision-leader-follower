from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from .plotting import save_occlusion_figure, save_range_figure, save_summary_figure, save_trajectory_figure
from .simulation import Config, simulate_trial


SCENARIOS = ("straight", "s_curve", "turn", "occlusion")
SEEDS = tuple(range(8))


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _median(records: list[dict], key: str) -> float:
    values = [float(row[key]) for row in records if np.isfinite(float(row[key]))]
    return float(np.median(values))


def run_experiments(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    cfg = Config()
    metrics: list[dict] = []
    representative: dict[str, list[dict]] = {}
    for scenario in SCENARIOS:
        for seed in SEEDS:
            rows, result = simulate_trial(seed, scenario, cfg)
            flat_result = {key: value for key, value in result.items() if key != "config"}
            metrics.append(flat_result)
            if seed == 0:
                representative[scenario] = rows

    metric_keys = ("range_rmse_m", "bearing_mae_deg", "estimated_range_rmse_m", "formation_rmse_m")
    summary = {
        "status": "toy kinematic baseline; not ROS 2 or Gazebo evidence",
        "trial_count": len(metrics),
        "scenarios": list(SCENARIOS),
        "seeds": list(SEEDS),
        "overall_median": {key: _median(metrics, key) for key in metric_keys},
        "occlusion_median_reacquisition_s": _median([row for row in metrics if row["scenario"] == "occlusion"], "reacquisition_s"),
        "collision_samples_total": int(sum(row["collision_samples"] for row in metrics)),
        "scenario_medians": {
            scenario: {key: _median([row for row in metrics if row["scenario"] == scenario], key) for key in metric_keys}
            for scenario in SCENARIOS
        },
        "config": result["config"],
    }

    _write_csv(output / "trial_metrics.csv", metrics)
    _write_csv(output / "representative_occlusion_timeseries.csv", representative["occlusion"])
    with (output / "summary.json").open("w", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2, sort_keys=True)
    save_range_figure(representative["occlusion"], output / "figure_1_range_baseline.png")
    save_trajectory_figure(representative["s_curve"], output / "figure_2_formation_tracking.png")
    save_occlusion_figure(representative["occlusion"], output / "figure_3_occlusion_recovery.png")
    save_summary_figure(summary, output / "figure_4_summary.png")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the deterministic EE 616 toy leader-follower baseline")
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    summary = run_experiments(args.output)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
