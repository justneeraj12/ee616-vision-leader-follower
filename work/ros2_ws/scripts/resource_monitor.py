#!/usr/bin/env python3
"""Sample container CPU, memory, and NVIDIA resources until a stop file exists."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def _integer(path: Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _cpu_usage_usec() -> int | None:
    path = Path("/sys/fs/cgroup/cpu.stat")
    try:
        fields = dict(
            line.split(maxsplit=1)
            for line in path.read_text(encoding="utf-8").splitlines()
        )
        return int(fields["usage_usec"])
    except (KeyError, OSError, ValueError):
        return None


def _gpu_sample() -> tuple[float | None, float | None]:
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=utilization.gpu,memory.used",
            "--format=csv,noheader,nounits",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None, None
    fields = result.stdout.strip().split(",")
    return float(fields[0].strip()), float(fields[1].strip())


def monitor(
    stop_file: Path,
    output: Path,
    interval_s: float,
    samples_output: Path | None = None,
) -> dict:
    """Collect resource maxima and return a summary."""
    started_wall = time.monotonic()
    started_cpu = _cpu_usage_usec()
    peak_memory = 0
    peak_gpu_util = 0.0
    peak_gpu_memory = 0.0
    samples = 0
    sample_rows = []
    previous_cpu = started_cpu
    previous_wall = started_wall
    while not stop_file.exists():
        sampled_wall = time.monotonic()
        sampled_cpu = _cpu_usage_usec()
        memory = _integer(Path("/sys/fs/cgroup/memory.current"))
        if memory is not None:
            peak_memory = max(peak_memory, memory)
        gpu_util, gpu_memory = _gpu_sample()
        if gpu_util is not None:
            peak_gpu_util = max(peak_gpu_util, gpu_util)
        if gpu_memory is not None:
            peak_gpu_memory = max(peak_gpu_memory, gpu_memory)
        interval_cpu_percent = None
        if (
            sampled_cpu is not None
            and previous_cpu is not None
            and sampled_wall > previous_wall
        ):
            interval_cpu_percent = (
                ((sampled_cpu - previous_cpu) / 1_000_000.0)
                / (sampled_wall - previous_wall)
                * 100.0
            )
        sample_rows.append({
            "elapsed_s": sampled_wall - started_wall,
            "cpu_core_equivalent_percent": interval_cpu_percent,
            "memory_mib": memory / (1024.0 * 1024.0) if memory is not None else None,
            "gpu_utilization_percent": gpu_util,
            "gpu_memory_mib": gpu_memory,
        })
        previous_cpu = sampled_cpu
        previous_wall = sampled_wall
        samples += 1
        time.sleep(interval_s)
    elapsed = time.monotonic() - started_wall
    ended_cpu = _cpu_usage_usec()
    cpu_core_percent = None
    if started_cpu is not None and ended_cpu is not None and elapsed > 0.0:
        cpu_core_percent = ((ended_cpu - started_cpu) / 1_000_000.0) / elapsed
        cpu_core_percent *= 100.0
    summary = {
        "cpu_core_equivalent_percent": cpu_core_percent,
        "elapsed_s": elapsed,
        "logical_cpu_count": os.cpu_count(),
        "peak_gpu_memory_mib": peak_gpu_memory,
        "peak_gpu_utilization_percent": peak_gpu_util,
        "peak_memory_mib": peak_memory / (1024.0 * 1024.0),
        "sample_count": samples,
        "scope": "container-level resource sample",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if samples_output is not None:
        samples_output.parent.mkdir(parents=True, exist_ok=True)
        with samples_output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "elapsed_s", "cpu_core_equivalent_percent", "memory_mib",
                    "gpu_utilization_percent", "gpu_memory_mib",
                ],
            )
            writer.writeheader()
            writer.writerows(sample_rows)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stop-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument("--samples-output", type=Path)
    args = parser.parse_args()
    print(json.dumps(monitor(
        args.stop_file,
        args.output,
        args.interval,
        args.samples_output,
    )))


if __name__ == "__main__":
    main()
