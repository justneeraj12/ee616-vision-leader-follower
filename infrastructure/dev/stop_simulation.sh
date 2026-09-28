#!/usr/bin/env bash
set -euo pipefail

patterns=(
    "ros2 launch ee616_simulation warehouse_playground.launch.py"
    "gz sim.*warehouse_playground.sdf"
    "parameter_bridge.*camera_bridge"
)

found=0
for pattern in "${patterns[@]}"; do
    if pgrep -u "$(id -u)" -f "${pattern}" >/dev/null; then
        found=1
        pkill -INT -u "$(id -u)" -f "${pattern}" || true
    fi
done

if [[ "${found}" -eq 1 ]]; then
    echo "Stop signal sent to the EE 616 playground processes."
else
    echo "No EE 616 playground processes were running."
fi
