#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash
cd /workspace/work/ros2_ws
colcon build --symlink-install --packages-select \
  ee616_simulation ee616_evaluation
source install/setup.bash

output_root=/workspace/work/ros2_ws/results/yolo_gate/v2_failure_diagnostics
for scene in camera_calibration straight_aisle; do
  ros2 launch ee616_evaluation yolo_dataset_capture.launch.py \
    scene:="$scene" split:=test output_dir:="$output_root" \
    capture_config:=yolo_failure_diagnostic.yaml
done

python3 /workspace/work/ros2_ws/scripts/diagnose_yolov8n_domain.py
