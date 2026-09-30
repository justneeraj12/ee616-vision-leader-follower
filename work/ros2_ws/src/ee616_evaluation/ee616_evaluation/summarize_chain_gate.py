"""Aggregate the staged incremental-chain evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics


def summarize(directory: Path, max_followers: int = 3) -> dict:
    paths = sorted(directory.glob("chain_*_run_*_summary.json"))
    runs = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    runs = [run for run in runs if run["follower_count"] <= max_followers]
    counts = range(2, max_followers + 1)
    cells = {
        (count, profile): [
            run for run in runs
            if run["follower_count"] == count and run["profile"] == profile
        ]
        for count in counts for profile in ("straight", "turn")
    }
    complete = len(runs) == 6 * (max_followers - 1) and all(len(items) == 3 for items in cells.values())
    results = {}
    for count in counts:
        count_runs = [run for run in runs if run["follower_count"] == count]
        followers = {}
        for index in range(1, count + 1):
            metrics = [run["followers"][str(index)] for run in count_runs]
            followers[str(index)] = {
                "spacing_rmse_m_mean": statistics.fmean(item["spacing_rmse_m"] for item in metrics) if metrics else None,
                "spacing_rmse_m_worst": max((item["spacing_rmse_m"] for item in metrics), default=None),
                "track_fraction_min": min((item["track_fraction"] for item in metrics), default=None),
                "collision_samples_total": sum(item["collision_samples"] for item in metrics),
                "control_period_p95_ms_worst": max((item["control_period_p95_ms"] for item in metrics), default=None),
                "inference_latency_p95_ms_worst": max(
                    (item["inference_latency_p95_ms"] for item in metrics if item["inference_latency_p95_ms"] is not None),
                    default=None,
                ),
            }
        results[str(count)] = {
            "run_count": len(count_runs),
            "followers": followers,
            "mean_rearward_rmse_delta_m": {
                f"follower_{index - 1}_to_{index}": (
                    followers[str(index)]["spacing_rmse_m_mean"]
                    - followers[str(index - 1)]["spacing_rmse_m_mean"]
                    if followers[str(index)]["spacing_rmse_m_mean"] is not None
                    and followers[str(index - 1)]["spacing_rmse_m_mean"] is not None
                    else None
                )
                for index in range(2, count + 1)
            },
        }
    resource_path = directory / "resources.json"
    resources = (
        json.loads(resource_path.read_text(encoding="utf-8"))
        if max_followers == 3 and resource_path.exists() else None
    )
    resource_ok = resources is None or resources["peak_gpu_memory_mib"] <= 4096.0
    passed = complete and all(run["status"] == "pass" for run in runs) and resource_ok
    return {
        "status": "pass" if passed else "fail",
        "run_count": len(runs),
        "expected_run_count": 6 * (max_followers - 1),
        "maximum_follower_count": max_followers,
        "chains": results,
        "resources": resources,
        "checks": {
            "three_runs_per_profile_and_chain_length": complete,
            "all_runs_pass": bool(runs) and all(run["status"] == "pass" for run in runs),
            "peak_gpu_memory_at_most_4_gib": resource_ok,
        },
        "ground_truth_boundary": "Gazebo pose truth was consumed only inside ee616_evaluation.",
        "scope": "Nominal straight and gradual-turn incremental chains; no disturbance or safety claim.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--max-followers", type=int, choices=(2, 3), default=3)
    args = parser.parse_args()
    summary = summarize(args.directory, args.max_followers)
    name = "stage_2_summary.json" if args.max_followers == 2 else "summary.json"
    (args.directory / name).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(0 if summary["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
