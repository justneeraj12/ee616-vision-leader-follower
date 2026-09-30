#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/jazzy/setup.bash
cd /workspace/work/ros2_ws
colcon build --symlink-install --packages-select \
  ee616_simulation ee616_evaluation
source install/setup.bash
set -u

dataset_root=/workspace/work/ros2_ws/datasets/ee616_predecessor_target_v2
capture_config=yolo_dataset_capture_v2.yaml

for scene in yolo_train_open yolo_train_aisle yolo_train_low_light; do
  ros2 launch ee616_evaluation yolo_dataset_capture.launch.py \
    scene:="$scene" split:=train output_dir:="$dataset_root" \
    capture_config:="$capture_config"
done
ros2 launch ee616_evaluation yolo_dataset_capture.launch.py \
  scene:=yolo_val_mixed split:=val output_dir:="$dataset_root" \
  capture_config:="$capture_config"
ros2 launch ee616_evaluation yolo_dataset_capture.launch.py \
  scene:=yolo_test_occlusion split:=test output_dir:="$dataset_root" \
  capture_config:="$capture_config"

ros2 run ee616_evaluation validate_yolo_dataset \
  "$dataset_root" \
  --output /workspace/work/ros2_ws/results/yolo_dataset/dataset_v2_manifest.json
