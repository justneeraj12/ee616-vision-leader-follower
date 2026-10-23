"""Aggregate pair-first and three-follower warehouse mission evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics


def summarize(directory: Path, max_followers: int = 3) -> dict:
    paths = sorted(directory.glob("warehouse_mission_*_run_*_summary.json"))
    runs = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    runs = [run for run in runs if run["follower_count"] <= max_followers]
    expected = {1: 1} if max_followers == 1 else {1: 1, 3: 3}
    complete = all(
        sum(run["follower_count"] == count for run in runs) == repetitions
        for count, repetitions in expected.items()
    ) and len(runs) == sum(expected.values())
    chains = {}
    for count in expected:
        count_runs = [run for run in runs if run["follower_count"] == count]
        followers = {}
        for index in range(1, count + 1):
            metrics = [run["followers"][str(index)] for run in count_runs]
            rmse = [item["transport_spacing_rmse_m"] for item in metrics]
            followers[str(index)] = {
                "transport_spacing_rmse_m_mean": statistics.fmean(rmse) if rmse else None,
                "transport_spacing_rmse_m_worst": max(rmse, default=None),
                "track_fraction_min": min(
                    (item["track_fraction"] for item in metrics), default=None
                ),
                "collision_samples_total": sum(
                    item["collision_samples"] for item in metrics
                ),
                "inference_latency_p95_ms_worst": max(
                    (
                        item["inference_latency_p95_ms"] for item in metrics
                        if item["inference_latency_p95_ms"] is not None
                    ),
                    default=None,
                ),
            }
        chains[str(count)] = {
            "run_count": len(count_runs),
            "followers": followers,
            "real_time_factor_min": min(
                (run["real_time_factor"] for run in count_runs), default=None
            ),
            "loading_station_error_m_worst": max(
                (
                    error for run in count_runs
                    for error in run["loading_station_max_error_m"].values()
                    if error is not None
                ),
                default=None,
            ),
            "warehouse_obstacle_collision_samples_total": sum(
                sum(run.get("warehouse_obstacle_collision_samples", {}).values())
                for run in count_runs
            ),
            "dropoff_station_error_m_worst": max(
                (
                    run["dropoff_station_final_error_m"]
                    for run in count_runs
                    if run.get("dropoff_station_final_error_m") is not None
                ),
                default=None,
            ),
        }
    resource_path = directory / "resources.json"
    resources = (
        json.loads(resource_path.read_text(encoding="utf-8"))
        if max_followers == 3 and resource_path.exists() else None
    )
    resource_ok = resources is None or (
        resources["peak_gpu_memory_mib"] <= 4096.0
        and resources["peak_memory_mib"] <= 12288.0
    )
    all_runs_pass = bool(runs) and all(run["status"] == "pass" for run in runs)
    passed = complete and all_runs_pass and resource_ok
    return {
        "status": "pass" if passed else "fail",
        "run_count": len(runs),
        "expected_runs": expected,
        "chains": chains,
        "resources": resources,
        "checks": {
            "pair_first_then_three_full_runs": complete,
            "all_runs_pass": all_runs_pass,
            "laptop_memory_limits": resource_ok,
        },
        "ground_truth_boundary": (
            "Gazebo pose truth was consumed only inside ee616_evaluation."
        ),
        "scope": (
            "Repeatable simulated formation transport with scripted visual cargo; "
            "not measured airport or warehouse throughput."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--max-followers", type=int, choices=(1, 3), default=3)
    args = parser.parse_args()
    summary = summarize(args.directory, args.max_followers)
    name = "pair_stage_summary.json" if args.max_followers == 1 else "summary.json"
    (args.directory / name).write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(0 if summary["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
