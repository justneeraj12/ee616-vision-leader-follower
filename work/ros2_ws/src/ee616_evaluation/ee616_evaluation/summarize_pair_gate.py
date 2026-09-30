"""Aggregate repeated one-pair runs without changing their raw evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics


def summarize(directory: Path) -> dict:
    paths = sorted(directory.glob("*_run_*_summary.json"))
    runs = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    profiles = {profile: [run for run in runs if run["profile"] == profile] for profile in ("straight", "turn")}
    complete = len(runs) == 6 and all(len(items) == 3 for items in profiles.values())
    passed = complete and all(run["status"] == "pass" for run in runs)
    return {
        "status": "pass" if passed else "fail",
        "run_count": len(runs),
        "expected_run_count": 6,
        "profiles": {
            profile: {
                "run_count": len(items),
                "spacing_rmse_m_mean": statistics.fmean(run["spacing_rmse_m"] for run in items) if items else None,
                "spacing_rmse_m_worst": max((run["spacing_rmse_m"] for run in items), default=None),
                "collision_samples_total": sum(run["collision_samples"] for run in items),
                "track_fraction_min": min((run["track_fraction"] for run in items), default=None),
                "control_period_p95_ms_worst": max((run["control_period_p95_ms"] for run in items), default=None),
            }
            for profile, items in profiles.items()
        },
        "checks": {
            "three_runs_per_profile": complete,
            "all_runs_pass": bool(runs) and all(run["status"] == "pass" for run in runs),
        },
        "ground_truth_boundary": "Gazebo pose truth was consumed only inside ee616_evaluation.",
        "scope": "Nominal straight and gradual-turn one-pair integration only.",
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
