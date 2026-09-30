#!/usr/bin/env bash
set -eo pipefail

work_root=/workspace/work/ros2_ws
stop_file=/tmp/ee616-yolo-v3-training-stop
resource_output="$work_root/results/yolo_gate/training_resources_v3.json"
rm -f "$stop_file"

export PYTORCH_ALLOC_CONF=expandable_segments:True
python3 "$work_root/scripts/resource_monitor.py" \
  --stop-file "$stop_file" \
  --output "$resource_output" \
  --interval 0.5 &
monitor_pid=$!

cleanup() {
  touch "$stop_file"
  wait "$monitor_pid" || true
}
trap cleanup EXIT

python3 "$work_root/scripts/train_yolov8n_v3.py"
