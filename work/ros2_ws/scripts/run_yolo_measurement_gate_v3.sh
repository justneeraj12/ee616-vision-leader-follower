#!/usr/bin/env bash
set -eo pipefail

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${workspace_dir}/results/yolo_measurement_gate_v3"
stop_file=/tmp/ee616-yolo-gate-v3-stop
resource_output="${output_dir}/resources.json"

source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source "${workspace_dir}/install/setup.bash"

mkdir -p "${output_dir}"
rm -f "${stop_file}"
python3 "${workspace_dir}/scripts/resource_monitor.py" \
  --stop-file "${stop_file}" \
  --output "${resource_output}" \
  --interval 0.5 &
monitor_pid=$!

cleanup() {
  touch "${stop_file}"
  wait "${monitor_pid}" || true
}
trap cleanup EXIT

for scene in yolo_final_open_v3 yolo_final_aisle_v3; do
  ros2 launch ee616_evaluation camera_measurement_experiment.launch.py \
    detector:=yolov8n yolo_config:=yolov8n_target_v3.yaml \
    scene:="${scene}" output_dir:="${output_dir}"
done

ros2 run ee616_evaluation summarize_camera_gate \
  --output-dir "${output_dir}" \
  --require-latency \
  --scope "Synchronized YOLOv8n v3 on sealed Gazebo scenes; not closed-loop control, physical-robot, or safety evidence"
