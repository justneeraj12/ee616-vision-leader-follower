#!/usr/bin/env bash
set -euo pipefail

patterns=(
    "ros2 launch ee616_simulation warehouse_playground.launch.py"
    "ros2 launch ee616_simulation scenario_playground.launch.py"
    "ros2 launch ee616_simulation aws_warehouse_benchmark.launch.py"
    "gz sim.*warehouse_playground.sdf"
    "gz sim.*generated_scenarios"
    "gz sim.*aws-no-roof"
    "gz sim.*generated_pair_worlds"
    "gz sim.*generated_chain_worlds"
    "gz sim.*generated_disturbance_worlds"
    "parameter_bridge.*camera_bridge"
    "demo_viewer"
    "professor_demo.launch.py"
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
