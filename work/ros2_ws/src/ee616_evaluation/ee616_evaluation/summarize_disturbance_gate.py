"""Aggregate the pair-first controlled-disturbance matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics


PAIR_SCENARIOS = (
    "sharp_turn", "short_occlusion", "long_occlusion",
    "leader_stop", "actuator_bias",
)


def summarize(directory: Path, stage: str = "full") -> dict:
    paths = sorted(directory.glob("disturbance_*_run_*_summary.json"))
    loaded = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    pair_runs = [run for run in loaded if run["follower_count"] == 1 and run["scenario"] in PAIR_SCENARIOS]
    chain_runs = [run for run in loaded if run["follower_count"] == 3 and run["scenario"] == "combined"]
    selected = pair_runs if stage == "pair" else pair_runs + chain_runs
    pair_cells = {scenario: [run for run in pair_runs if run["scenario"] == scenario] for scenario in PAIR_SCENARIOS}
    pair_complete = len(pair_runs) == 15 and all(len(items) == 3 for items in pair_cells.values())
    chain_complete = len(chain_runs) == 3
    complete = pair_complete and (stage == "pair" or chain_complete)
    groups = {}
    for count, scenario in sorted({(run["follower_count"], run["scenario"]) for run in selected}):
        runs = [run for run in selected if run["follower_count"] == count and run["scenario"] == scenario]
        followers = {}
        for index in range(1, count + 1):
            metrics = [run["followers"][str(index)] for run in runs]
            followers[str(index)] = {
                "spacing_rmse_m_mean": statistics.fmean(item["spacing_rmse_m"] for item in metrics),
                "spacing_rmse_m_worst": max(item["spacing_rmse_m"] for item in metrics),
                "track_fraction_min": min(item["track_fraction"] for item in metrics),
                "collision_samples_total": sum(item["collision_samples"] for item in metrics),
                "control_period_p95_ms_worst": max(item["control_period_p95_ms"] for item in metrics),
                "inference_latency_p95_ms_worst": max(
                    item["inference_latency_p95_ms"] for item in metrics
                    if item["inference_latency_p95_ms"] is not None
                ),
            }
        groups[f"{count}_{scenario}"] = {"run_count": len(runs), "followers": followers}
    resource_path = directory / "resources.json"
    resources = (
        json.loads(resource_path.read_text(encoding="utf-8"))
        if stage == "full" and resource_path.exists() else None
    )
    resource_ok = resources is None or resources["peak_gpu_memory_mib"] <= 4096.0
    all_pass = bool(selected) and all(run["status"] == "pass" for run in selected)
    return {
        "status": "pass" if complete and all_pass and resource_ok else "fail",
        "stage": stage,
        "run_count": len(selected),
        "expected_run_count": 15 if stage == "pair" else 18,
        "groups": groups,
        "resources": resources,
        "checks": {
            "pair_matrix_complete": pair_complete,
            "three_follower_combined_complete": True if stage == "pair" else chain_complete,
            "all_runs_pass": all_pass,
            "peak_gpu_memory_at_most_4_gib": resource_ok,
        },
        "ground_truth_boundary": "Gazebo pose truth was consumed only inside ee616_evaluation.",
        "scope": "Controlled simulation disturbances only; no physical-robot or safety claim.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--stage", choices=("pair", "full"), default="full")
    args = parser.parse_args()
    summary = summarize(args.directory, args.stage)
    name = "pair_stage_summary.json" if args.stage == "pair" else "summary.json"
    (args.directory / name).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(0 if summary["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
