#!/usr/bin/env python3
"""Verify and aggregate the post-freeze convoy-governance evidence."""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path
from typing import Any


EXPECTED_GROUPS = {
    "sparse_wide_nominal_1f": {"count": 3, "kind": "mission"},
    "sparse_wide_containment_3f": {"count": 3, "kind": "chain_safety"},
    "sparse_wide_leader_dropout_1f": {
        "count": 3,
        "kind": "mission",
        "fault": True,
    },
}


def _load_group(root: Path, name: str) -> list[dict[str, Any]]:
    paths = sorted((root / name).glob("*_summary.json"))
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _verify_ground_truth_boundary(summary: dict[str, Any]) -> None:
    _require(
        summary["governor"]["ground_truth_used"] is False,
        "governor reported a ground-truth dependency",
    )
    boundary = summary["ground_truth_boundary"]
    _require(
        "was read only by ee616_evaluation" in boundary
        and "was not published to perception, estimation, supervision, or control"
        in boundary,
        "evaluation-only ground-truth boundary is missing",
    )


def _verify_accepted(summary: dict[str, Any], *, fault: bool) -> None:
    _require(summary["status"] == "pass", str(summary.get("failure")))
    _require(
        not any(summary["warehouse_obstacle_collision_samples"].values()),
        "warehouse obstacle collision samples were recorded",
    )
    _verify_ground_truth_boundary(summary)
    _require(
        all(summary["mission_checks"].values()),
        "one or more mission checks failed",
    )
    _require(
        all(
            all(follower["checks"].values())
            for follower in summary["followers"].values()
        ),
        "one or more follower checks failed",
    )
    if fault:
        fault_samples = summary["governor"]["fault_samples"]
        zero_samples = summary["governor"]["fault_zero_command_samples"]
        _require(fault_samples > 0, "leader dropout was not observed")
        _require(
            zero_samples == fault_samples,
            "leader output was nonzero during one or more dropout samples",
        )


def _verify_containment(summary: dict[str, Any]) -> None:
    _require(summary["status"] == "fail", "containment run unexpectedly passed")
    _require(
        not any(summary["warehouse_obstacle_collision_samples"].values()),
        "warehouse obstacle collision samples were recorded",
    )
    _verify_ground_truth_boundary(summary)
    _require(
        "HOLD" in summary["governor"]["mode_sequence"],
        "convoy HOLD was not observed",
    )
    _require(
        summary["mission_checks"]["route_complete"] is False,
        "containment boundary did not retain the expected incomplete route",
    )
    _require(
        all(
            follower["bounded_commands"]
            for follower in summary["followers"].values()
        ),
        "one or more follower commands exceeded configured bounds",
    )


def verify(root: Path) -> dict[str, Any]:
    aggregate: dict[str, Any] = {
        "experiment": "convoy_governance_gate",
        "status": "pass",
        "accepted_mission_run_count": 0,
        "chain_completed_run_count": 0,
        "chain_contained_stop_run_count": 0,
        "groups": {},
        "ground_truth_boundary": (
            "Gazebo truth is consumed only by ee616_evaluation and never by "
            "perception, estimation, supervision, or control."
        ),
    }
    for name, expected in EXPECTED_GROUPS.items():
        summaries = _load_group(root, name)
        _require(
            len(summaries) == expected["count"],
            f"{name}: expected {expected['count']} summaries, got {len(summaries)}",
        )
        statuses = [summary["status"] for summary in summaries]
        if expected["kind"] == "mission":
            for summary in summaries:
                _verify_accepted(summary, fault=expected.get("fault", False))
            aggregate["accepted_mission_run_count"] += len(summaries)
        elif expected["kind"] == "chain_safety":
            for summary in summaries:
                if summary["status"] == "pass":
                    _verify_accepted(summary, fault=False)
                    aggregate["chain_completed_run_count"] += 1
                else:
                    _verify_containment(summary)
                    aggregate["chain_contained_stop_run_count"] += 1

        follower_rmse: dict[str, list[float]] = {}
        follower_track: dict[str, list[float]] = {}
        for summary in summaries:
            for follower_id, metrics in summary["followers"].items():
                follower_rmse.setdefault(follower_id, []).append(
                    metrics["transport_spacing_rmse_m"]
                )
                follower_track.setdefault(follower_id, []).append(
                    metrics["track_fraction"]
                )
        aggregate["groups"][name] = {
            "acceptance_kind": expected["kind"],
            "run_count": len(summaries),
            "statuses": statuses,
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

    output = root / "aggregate_summary.json"
    output.write_text(json.dumps(aggregate, indent=2) + "\n", encoding="utf-8")
    return aggregate


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_convoy_governance_gate.py EVIDENCE_DIR", file=sys.stderr)
        return 2
    try:
        aggregate = verify(Path(sys.argv[1]))
    except (AssertionError, KeyError, OSError, TypeError, ValueError) as exc:
        print(f"completion evidence verification failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(aggregate, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
