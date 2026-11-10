#!/usr/bin/env python3
"""Verify and aggregate repeated bounded SEARCH recovery evidence."""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path
from typing import Any


EXPECTED_GROUPS = {
    "sparse_wide_nominal_1f": {"count": 3, "pair": True},
    "sparse_wide_nominal_3f": {"count": 3},
    "sparse_wide_leader_dropout_3f": {"count": 3, "fault": True},
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _load_group(root: Path, name: str) -> list[dict[str, Any]]:
    paths = sorted((root / name).glob("*_summary.json"))
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]


def _verify_boundary(summary: dict[str, Any]) -> None:
    governor = summary.get("governor")
    if governor is not None:
        _require(
            governor["ground_truth_used"] is False,
            "governor reported a ground-truth dependency",
        )
    else:
        _require(
            summary.get("ground_truth_read_failures", {}).get(
                "total_failed_samples"
            )
            == 0,
            "disturbance evaluator did not maintain its truth-reading boundary",
        )
    text = summary["ground_truth_boundary"]
    _require(
        "was read only by ee616_evaluation" in text
        and "was not published" in text
        and all(
            subsystem in text
            for subsystem in ("perception", "estimation", "supervision", "control")
        ),
        "evaluation-only ground-truth boundary is missing",
    )


def _verify_recovered_run(summary: dict[str, Any], *, fault: bool) -> None:
    _require(
        summary["mission_checks"]["route_complete"] is True,
        "route did not complete",
    )
    _require(
        not any(summary["warehouse_obstacle_collision_samples"].values()),
        "warehouse obstacle collision samples were recorded",
    )
    _verify_boundary(summary)
    for follower_id, follower in summary["followers"].items():
        _require(
            follower["collision_samples"] == 0,
            f"follower_{follower_id} collision samples were recorded",
        )
        _require(
            follower["bounded_commands"],
            f"follower_{follower_id} exceeded configured command bounds",
        )
        _require(
            follower["search_linear_zero"],
            f"follower_{follower_id} moved forward during SEARCH",
        )
        _require(
            follower["search_yaw_bounded"],
            f"follower_{follower_id} exceeded the SEARCH yaw bound",
        )
    if fault:
        fault_samples = summary["governor"]["fault_samples"]
        zero_samples = summary["governor"]["fault_zero_command_samples"]
        _require(fault_samples > 0, "leader dropout was not observed")
        _require(
            zero_samples == fault_samples,
            "leader output was nonzero during one or more dropout samples",
        )


def _failed_checks(summary: dict[str, Any]) -> list[str]:
    failures = [
        f"mission.{name}"
        for name, passed in summary["mission_checks"].items()
        if not passed
    ]
    for follower_id, follower in summary["followers"].items():
        failures.extend(
            f"follower_{follower_id}.{name}"
            for name, passed in follower["checks"].items()
            if not passed
        )
    return failures


def _verify_controlled_search(root: Path) -> dict[str, Any]:
    paths = sorted((root / "pair_visual_blackout").glob("*_summary.json"))
    _require(len(paths) == 1, "expected one controlled visual-blackout summary")
    summary = json.loads(paths[0].read_text(encoding="utf-8"))
    _require(summary["status"] == "pass", "controlled visual-blackout run failed")
    _require(summary["route_complete"] is True, "controlled search route did not complete")
    follower = summary["followers"]["1"]
    _require(follower["search_samples"] > 0, "controlled run did not enter SEARCH")
    _require(
        follower["reacquire_samples"] > 0,
        "controlled run did not enter REACQUIRE",
    )
    _require(follower["search_linear_zero"], "controlled SEARCH moved forward")
    _require(follower["search_yaw_bounded"], "controlled SEARCH yaw was unbounded")
    _require(
        follower["collision_samples"] == 0,
        "controlled search recorded collision samples",
    )
    _verify_boundary(summary)
    return {
        "status": summary["status"],
        "route_complete": summary["route_complete"],
        "search_sample_count": follower["search_samples"],
        "reacquire_sample_count": follower["reacquire_samples"],
        "spacing_rmse_m": follower["spacing_rmse_m"],
        "track_fraction": follower["track_fraction"],
        "collision_samples": follower["collision_samples"],
    }


def verify(root: Path) -> dict[str, Any]:
    controlled_search = _verify_controlled_search(root)
    aggregate: dict[str, Any] = {
        "experiment": "bounded_search_recovery_gate",
        "status": "pass",
        "controlled_run_count": 1,
        "run_count": 0,
        "route_completed_run_count": 0,
        "strict_evaluator_pass_count": 0,
        "search_sample_count": 0,
        "reacquire_sample_count": 0,
        "groups": {},
        "acceptance_note": (
            "This gate requires completed routes, zero sampled collisions, "
            "bounded zero-forward SEARCH, and complete fault containment. "
            "The unchanged evaluator's stricter spacing and TRACK-fraction "
            "verdict is reported separately and is not relaxed."
        ),
        "ground_truth_boundary": (
            "Gazebo truth is consumed only by ee616_evaluation and never by "
            "perception, estimation, supervision, or control."
        ),
        "controlled_search": controlled_search,
    }
    for name, expected in EXPECTED_GROUPS.items():
        summaries = _load_group(root, name)
        _require(
            len(summaries) == expected["count"],
            f"{name}: expected {expected['count']} summaries, got {len(summaries)}",
        )
        for summary in summaries:
            _verify_recovered_run(summary, fault=expected.get("fault", False))
        if expected.get("pair"):
            _require(
                all(summary["status"] == "pass" for summary in summaries),
                "one or more validated pair runs failed the strict evaluator",
            )

        follower_rmse: dict[str, list[float]] = {}
        follower_track: dict[str, list[float]] = {}
        search_samples = 0
        reacquire_samples = 0
        for summary in summaries:
            for follower_id, metrics in summary["followers"].items():
                follower_rmse.setdefault(follower_id, []).append(
                    metrics["transport_spacing_rmse_m"]
                )
                follower_track.setdefault(follower_id, []).append(
                    metrics["track_fraction"]
                )
                search_samples += metrics["search_samples"]
                reacquire_samples += metrics["reacquire_samples"]
        strict_pass_count = sum(
            summary["status"] == "pass" for summary in summaries
        )
        aggregate["run_count"] += len(summaries)
        aggregate["route_completed_run_count"] += len(summaries)
        aggregate["strict_evaluator_pass_count"] += strict_pass_count
        aggregate["search_sample_count"] += search_samples
        aggregate["reacquire_sample_count"] += reacquire_samples
        aggregate["groups"][name] = {
            "run_count": len(summaries),
            "evaluator_statuses": [summary["status"] for summary in summaries],
            "strict_evaluator_pass_count": strict_pass_count,
            "failed_checks_by_run": [
                _failed_checks(summary) for summary in summaries
            ],
            "minimum_real_time_factor": min(
                summary["real_time_factor"] for summary in summaries
            ),
            "mean_spacing_rmse_m": {
                follower_id: statistics.fmean(values)
                for follower_id, values in follower_rmse.items()
            },
            "maximum_spacing_rmse_m": {
                follower_id: max(values)
                for follower_id, values in follower_rmse.items()
            },
            "minimum_track_fraction": {
                follower_id: min(values)
                for follower_id, values in follower_track.items()
            },
            "search_sample_count": search_samples,
            "reacquire_sample_count": reacquire_samples,
            "warehouse_obstacle_collision_sample_total": sum(
                sum(summary["warehouse_obstacle_collision_samples"].values())
                for summary in summaries
            ),
            "fault_samples": sum(
                summary["governor"]["fault_samples"] for summary in summaries
            ),
            "fault_zero_command_samples": sum(
                summary["governor"]["fault_zero_command_samples"]
                for summary in summaries
            ),
        }
    if aggregate["strict_evaluator_pass_count"] < aggregate["run_count"]:
        aggregate["status"] = "pass_with_metric_limits"
    aggregate["total_run_count"] = aggregate["run_count"] + 1
    aggregate["total_route_completed_run_count"] = (
        aggregate["route_completed_run_count"] + 1
    )
    (root / "aggregate_summary.json").write_text(
        json.dumps(aggregate, indent=2) + "\n", encoding="utf-8"
    )
    return aggregate


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_search_recovery_gate.py EVIDENCE_DIR", file=sys.stderr)
        return 2
    try:
        aggregate = verify(Path(sys.argv[1]))
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"search-recovery evidence verification failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(aggregate, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
