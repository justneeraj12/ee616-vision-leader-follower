#!/usr/bin/env bash
set -euo pipefail

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${workspace_dir}/results/camera_measurement_gate"

source /opt/ros/jazzy/setup.bash
source "${workspace_dir}/install/setup.bash"

mkdir -p "${output_dir}"
for scene in camera_calibration straight_aisle; do
  ros2 launch ee616_evaluation camera_measurement_experiment.launch.py \
    scene:="${scene}" output_dir:="${output_dir}"
done

ros2 run ee616_evaluation summarize_camera_gate --output-dir "${output_dir}"
