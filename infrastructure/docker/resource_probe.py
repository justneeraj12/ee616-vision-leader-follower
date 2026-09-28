#!/usr/bin/env python3
"""Write a small machine-readable container resource snapshot."""

import argparse
import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def memory_snapshot():
    """Return selected values from Linux procfs in kilobytes."""
    values = {}
    for line in Path('/proc/meminfo').read_text(encoding='utf-8').splitlines():
        key, value = line.split(':', maxsplit=1)
        if key in {'MemTotal', 'MemAvailable', 'SwapTotal', 'SwapFree'}:
            values[f'{key.lower()}_kb'] = int(value.strip().split()[0])
    return values


def gpu_snapshot():
    """Query NVIDIA resources when the GPU runtime is available."""
    if not shutil.which('nvidia-smi'):
        return {'available_in_container': False}
    command = [
        'nvidia-smi',
        '--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu',
        '--format=csv,noheader,nounits',
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    return {
        'available_in_container': result.returncode == 0,
        'query': result.stdout.strip() or None,
        'error': result.stderr.strip() or None,
    }


def main():
    """Collect and write the snapshot."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    snapshot = {
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'platform': platform.platform(),
        'logical_cpu_count': os.cpu_count(),
        'load_average': os.getloadavg(),
        'memory': memory_snapshot(),
        'gpu': gpu_snapshot(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )


if __name__ == '__main__':
    main()
