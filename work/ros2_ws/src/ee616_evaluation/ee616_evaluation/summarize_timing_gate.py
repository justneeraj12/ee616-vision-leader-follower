"""Aggregate three Gate 6 target-laptop timing runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics


STAGES = (
    "camera_to_measurement",
    "measurement_to_controller_cmd",
    "controller_to_actual_cmd",
    "detector_inference",
    "control_period",
)


def summarize(directory: Path) -> dict:
    timing_paths = sorted(directory.glob("timing_3_combined_run_*_summary.json"))
    behavior_paths = sorted(directory.glob("disturbance_3_combined_run_*_summary.json"))
    timing_runs = [json.loads(path.read_text(encoding="utf-8")) for path in timing_paths]
    behavior_runs = [json.loads(path.read_text(encoding="utf-8")) for path in behavior_paths]
    followers = {}
    for index in range(1, 4):
        metrics = [run["followers"][str(index)] for run in timing_runs]
        stage_metrics = {}
        for stage in STAGES:
            summaries = [item["latency"][stage] for item in metrics]
            stage_metrics[stage] = {
                "sample_count_total": sum(item["count"] for item in summaries),
                "p95_ms_worst": max(
                    (item["p95_ms"] for item in summaries if item["p95_ms"] is not None),
                    default=None,
                ),
                "p99_ms_worst": max(
                    (item["p99_ms"] for item in summaries if item["p99_ms"] is not None),
                    default=None,
                ),
                "max_ms_worst": max(
                    (item["max_ms"] for item in summaries if item["max_ms"] is not None),
                    default=None,
                ),
            }
        followers[str(index)] = {
            "camera_rate_hz_mean": statistics.fmean(
                item["camera_rate_hz"] for item in metrics
            ) if metrics else None,
            "measurement_rate_hz_mean": statistics.fmean(
                item["measurement_rate_hz"] for item in metrics
            ) if metrics else None,
            "measurement_delivery_ratio_min": min(
                (item["measurement_delivery_ratio"] for item in metrics),
                default=None,
            ),
            "latency": stage_metrics,
        }
    resources_path = directory / "resources.json"
    resource_samples_path = directory / "resource_samples.csv"
    resources = (
        json.loads(resources_path.read_text(encoding="utf-8"))
        if resources_path.exists() else None
    )
    real_time_factors = [run["real_time_factor"] for run in timing_runs]
    matrix_complete = len(timing_runs) == 3 and len(behavior_runs) == 3
    checks = {
        "three_timing_runs_complete": len(timing_runs) == 3,
        "three_behavior_runs_complete": len(behavior_runs) == 3,
        "all_timing_runs_pass": bool(timing_runs) and all(
            run["status"] == "pass" for run in timing_runs
        ),
        "accepted_behavior_unchanged": bool(behavior_runs) and all(
            run["status"] == "pass" for run in behavior_runs
        ),
        "resource_summary_present": resources is not None,
        "resource_samples_present": resource_samples_path.exists(),
        "peak_gpu_memory_at_most_4_gib": (
            resources is not None and resources["peak_gpu_memory_mib"] <= 4096.0
        ),
        "peak_container_memory_at_most_12_gib": (
            resources is not None and resources["peak_memory_mib"] <= 12288.0
        ),
    }
    return {
        "status": "pass" if matrix_complete and all(checks.values()) else "fail",
        "run_count": len(timing_runs),
        "expected_run_count": 3,
        "scenario": "combined",
        "follower_count": 3,
        "followers": followers,
        "real_time_factor_min": min(real_time_factors, default=None),
        "real_time_factor_mean": (
            statistics.fmean(real_time_factors) if real_time_factors else None
        ),
        "resources": resources,
        "checks": checks,
        "measurement_note": (
            "Observer-side wall-clock latency on one laptop; this does not include "
            "a network link or physical actuator response."
        ),
        "ground_truth_boundary": (
            "Timing observation used ROS topics only. Gazebo pose truth was consumed "
            "only by the separate behavior evaluator."
        ),
        "scope": "Simulation timing and resources on the target laptop only.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    summary = summarize(args.directory)
    (args.directory / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(0 if summary["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
