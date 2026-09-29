#!/usr/bin/env python3
"""Measure Gazebo real-time factor and container resources for one fixed run."""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


FATAL_LOG_PATTERNS = (
    "unable to find uri",
    "unable to resolve uri",
    "failed to load system plugin",
    "error code 12",
    "does not exist in the model path",
)


def _read_integer(paths: tuple[Path, ...]) -> int | None:
    for path in paths:
        try:
            return int(path.read_text(encoding="utf-8").strip())
        except (FileNotFoundError, PermissionError, ValueError):
            continue
    return None


def _memory_bytes() -> int | None:
    return _read_integer(
        (
            Path("/sys/fs/cgroup/memory.current"),
            Path("/sys/fs/cgroup/memory/memory.usage_in_bytes"),
        )
    )


def _cpu_usage_seconds() -> float | None:
    cpu_stat = Path("/sys/fs/cgroup/cpu.stat")
    try:
        values = dict(
            line.split(maxsplit=1)
            for line in cpu_stat.read_text(encoding="utf-8").splitlines()
        )
        return int(values["usage_usec"]) / 1_000_000.0
    except (FileNotFoundError, PermissionError, KeyError, ValueError):
        nanoseconds = _read_integer((Path("/sys/fs/cgroup/cpuacct/cpuacct.usage"),))
        return None if nanoseconds is None else nanoseconds / 1_000_000_000.0


def _gpu_sample() -> dict[str, float] | None:
    if not shutil.which("nvidia-smi"):
        return None
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=memory.used,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    first_gpu = result.stdout.splitlines()[0]
    try:
        memory_mib, utilization_percent = (
            float(value.strip()) for value in first_gpu.split(",", maxsplit=1)
        )
    except ValueError:
        return None
    return {
        "memory_used_mib": memory_mib,
        "utilization_percent": utilization_percent,
    }


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = round((len(ordered) - 1) * fraction)
    return ordered[index]


def _parse_stats(output: str) -> list[dict]:
    messages = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            messages.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return messages


def _scan_launch_log(path: Path) -> list[str]:
    if not path.is_file():
        return ["launch log missing"]
    matches = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        lowered = line.lower()
        if any(pattern in lowered for pattern in FATAL_LOG_PATTERNS):
            matches.append(line.strip())
    return matches


def measure(args: argparse.Namespace) -> dict:
    camera = json.loads(args.camera_json.read_text(encoding="utf-8"))
    command = [
        "gz",
        "topic",
        "-e",
        "--json-output",
        "-t",
        args.stats_topic,
        "-d",
        str(args.duration_seconds),
    ]
    start_wall = time.monotonic()
    start_cpu = _cpu_usage_seconds()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    memory_samples = []
    gpu_samples = []
    while process.poll() is None:
        memory = _memory_bytes()
        if memory is not None:
            memory_samples.append(memory)
        gpu = _gpu_sample()
        if gpu is not None:
            gpu_samples.append(gpu)
        time.sleep(0.5)
    stdout, stderr = process.communicate()
    elapsed = time.monotonic() - start_wall
    end_cpu = _cpu_usage_seconds()
    if process.returncode != 0:
        raise RuntimeError(f"Gazebo statistics command failed: {stderr.strip()}")

    messages = _parse_stats(stdout)
    rtf_values = [
        float(message["realTimeFactor"])
        for message in messages
        if "realTimeFactor" in message
    ]
    if not rtf_values:
        raise RuntimeError("No real-time-factor samples were received.")

    camera_rate = float(camera.get("measured_receive_hz") or 0.0)
    fatal_log_matches = _scan_launch_log(args.launch_log)
    memory_peak_mib = (
        max(memory_samples) / (1024.0 * 1024.0) if memory_samples else None
    )
    gpu_memory_peak = (
        max(sample["memory_used_mib"] for sample in gpu_samples)
        if gpu_samples
        else None
    )
    gpu_utilization_peak = (
        max(sample["utilization_percent"] for sample in gpu_samples)
        if gpu_samples
        else None
    )
    cpu_core_equivalent_percent = None
    if start_cpu is not None and end_cpu is not None and elapsed > 0:
        cpu_core_equivalent_percent = 100.0 * (end_cpu - start_cpu) / elapsed

    acceptance = {
        "camera_probe_passed": camera.get("status") == "pass",
        "camera_rate_at_least_14_25_hz": camera_rate >= 14.25,
        "rtf_median_at_least_0_95": statistics.median(rtf_values) >= 0.95,
        "rtf_p05_at_least_0_85": _percentile(rtf_values, 0.05) >= 0.85,
        "container_memory_peak_below_12_gib": (
            memory_peak_mib is not None and memory_peak_mib < 12 * 1024
        ),
        "gpu_memory_peak_below_3584_mib_if_available": (
            None if gpu_memory_peak is None else gpu_memory_peak < 3584
        ),
        "no_fatal_asset_or_plugin_errors": not fatal_log_matches,
    }
    required_results = [value for value in acceptance.values() if value is not None]
    return {
        "status": "pass" if all(required_results) else "fail",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "AWS no-roof visual and resource stress test; not control evidence",
        "duration_requested_seconds": args.duration_seconds,
        "duration_observed_seconds": elapsed,
        "stats_topic": args.stats_topic,
        "stats_samples": len(rtf_values),
        "real_time_factor": {
            "median": statistics.median(rtf_values),
            "p05": _percentile(rtf_values, 0.05),
            "minimum": min(rtf_values),
            "maximum": max(rtf_values),
        },
        "camera": camera,
        "estimated_camera_drop_fraction": max(0.0, 1.0 - camera_rate / 15.0),
        "resources": {
            "container_memory_peak_mib": memory_peak_mib,
            "cpu_core_equivalent_percent": cpu_core_equivalent_percent,
            "gpu_available_to_nvidia_smi": bool(gpu_samples),
            "gpu_memory_peak_mib": gpu_memory_peak,
            "gpu_utilization_peak_percent": gpu_utilization_peak,
            "gpu_rendering_acceleration_verified": False,
        },
        "fatal_log_matches": fatal_log_matches,
        "acceptance": acceptance,
        "limitations": [
            "Camera drop fraction is estimated from receive rate, not sequence numbers.",
            "Container CPU and memory include benchmark and ROS support processes.",
            "NVIDIA visibility does not prove Gazebo used hardware rendering.",
            "No detector or follower controller runs in this benchmark.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stats-topic", required=True)
    parser.add_argument("--duration-seconds", type=float, default=20.0)
    parser.add_argument("--camera-json", type=Path, required=True)
    parser.add_argument("--launch-log", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = measure(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
