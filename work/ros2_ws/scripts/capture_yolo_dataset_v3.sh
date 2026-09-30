#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/jazzy/setup.bash
cd /workspace/work/ros2_ws
colcon build --symlink-install --packages-select \
  ee616_simulation ee616_evaluation
source install/setup.bash
set -u

dataset_root=/workspace/work/ros2_ws/datasets/ee616_predecessor_target_v3
capture_config=yolo_dataset_capture_v3.yaml
expected_conditions=143

capture_scene() {
  local scene=$1
  local split=$2
  local metadata="$dataset_root/metadata/${split}_${scene}.json"
  local start_index=0
  local attempt

  if [[ -f "$metadata" ]]; then
    start_index=$(python3 -c \
      'import json,sys; print(len(json.load(open(sys.argv[1]))["records"]))' \
      "$metadata")
  fi
  if [[ "$start_index" -eq "$expected_conditions" ]]; then
    echo "Dataset scene already complete: $split/$scene"
    return
  fi

  for attempt in 1 2 3; do
    echo "Capturing $split/$scene from condition $start_index (attempt $attempt/3)"
    ros2 launch ee616_evaluation yolo_dataset_capture.launch.py \
      scene:="$scene" split:="$split" output_dir:="$dataset_root" \
      capture_config:="$capture_config" start_condition_index:="$start_index"
    start_index=$(python3 -c \
      'import json,sys; print(len(json.load(open(sys.argv[1]))["records"]))' \
      "$metadata")
    if [[ "$start_index" -eq "$expected_conditions" ]]; then
      return
    fi
  done
  echo "Dataset scene remained incomplete after three attempts: $split/$scene" >&2
  return 1
}

for scene in \
  yolo_train_open yolo_train_aisle yolo_train_low_light \
  yolo_train_bright yolo_train_neutral; do
  capture_scene "$scene" train
done
capture_scene yolo_val_v3 val
capture_scene yolo_test_v3 test

python3 /workspace/work/ros2_ws/scripts/filter_occluded_yolo_labels.py \
  "$dataset_root" \
  --output /workspace/work/ros2_ws/results/yolo_dataset/dataset_v3_visibility_filter.json \
  --apply

python3 /workspace/work/ros2_ws/scripts/verify_yolo_dataset_alignment.py \
  "$dataset_root" \
  --output /workspace/work/ros2_ws/results/yolo_dataset/dataset_v3_alignment.json

ros2 run ee616_evaluation validate_yolo_dataset \
  "$dataset_root" \
  --output /workspace/work/ros2_ws/results/yolo_dataset/dataset_v3_manifest.json
