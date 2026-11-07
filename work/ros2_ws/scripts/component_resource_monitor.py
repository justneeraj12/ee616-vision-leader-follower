#!/usr/bin/env python3
"""Record process-group resource attribution for the convoy governance gate."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import subprocess
import time
from pathlib import Path


GROUPS = {
    "leader_navigation": (
        "planner_server", "controller_server", "amcl", "map_server",
        "leader_map_tf", "warehouse_nav_mission", "convoy_governor",
    ),
    "follower_perception_control": (
        "yolo_measurement", "follower_controller",
    ),
    "simulation_evaluation": (
        "gz sim", "parameter_bridge", "mission_evaluator",
    ),
}


def sample_processes() -> dict[str, dict[str, float]]:
    """Return aggregate RSS and CPU by functional process group."""
    values = {
        group: {"cpu_percent": 0.0, "memory_mib": 0.0, "process_count": 0}
        for group in GROUPS
    }
    result = subprocess.run(
        ["ps", "-eo", "rss=,pcpu=,args="],
        capture_output=True,
        check=True,
        text=True,
        timeout=1.0,
    )
    for line in result.stdout.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) != 3:
            continue
        rss_kib, cpu_percent, command = parts
        for group, tokens in GROUPS.items():
            if any(token in command for token in tokens):
                values[group]["cpu_percent"] += float(cpu_percent)
                values[group]["memory_mib"] += float(rss_kib) / 1024.0
                values[group]["process_count"] += 1
                break
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stop-file", type=Path, required=True)
    parser.add_argument("--samples-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    parser.add_argument("--interval", type=float, default=0.5)
    args = parser.parse_args()
    args.samples_output.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    started = time.monotonic()
    while not args.stop_file.exists():
        try:
            grouped = sample_processes()
        except (OSError, subprocess.SubprocessError, ValueError):
            time.sleep(args.interval)
            continue
        elapsed = time.monotonic() - started
        for group, values in grouped.items():
            rows.append({"elapsed_s": elapsed, "group": group, **values})
        time.sleep(args.interval)
    fields = ["elapsed_s", "group", "cpu_percent", "memory_mib", "process_count"]
    with args.samples_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    summary = {}
    for group in GROUPS:
        group_rows = [row for row in rows if row["group"] == group]
        summary[group] = {
            "sample_count": len(group_rows),
            "peak_cpu_percent": max(
                (row["cpu_percent"] for row in group_rows), default=None
            ),
            "median_cpu_percent": statistics.median(
                [row["cpu_percent"] for row in group_rows]
            ) if group_rows else None,
            "peak_memory_mib": max(
                (row["memory_mib"] for row in group_rows), default=None
            ),
            "median_memory_mib": statistics.median(
                [row["memory_mib"] for row in group_rows]
            ) if group_rows else None,
        }
    args.summary_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
