#!/usr/bin/env bash
set -eo pipefail

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${workspace_dir}/results/warehouse_mission"
stop_file=/tmp/ee616-warehouse-mission-stop
resource_output="${output_dir}/resources.json"
resource_samples="${output_dir}/resource_samples.csv"

source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select \
  ee616_simulation ee616_perception ee616_control ee616_evaluation
source "${workspace_dir}/install/setup.bash"

mkdir -p "${output_dir}"
rm -f "${stop_file}"
python3 "${workspace_dir}/scripts/resource_monitor.py" \
  --stop-file "${stop_file}" --output "${resource_output}" \
  --samples-output "${resource_samples}" --interval 0.5 &
monitor_pid=$!

stop_monitor() {
  touch "${stop_file}"
  wait "${monitor_pid}" || true
}
trap stop_monitor EXIT

# Scientific staging: the validated pair is required before the target convoy.
ros2 launch ee616_evaluation warehouse_mission.launch.py \
  follower_count:=1 run_id:=run_01 output_dir:="${output_dir}"
ros2 run ee616_evaluation summarize_warehouse_mission \
  "${output_dir}" --max-followers 1

for repetition in 01 02 03; do
  ros2 launch ee616_evaluation warehouse_mission.launch.py \
    follower_count:=3 run_id:="run_${repetition}" output_dir:="${output_dir}"
done

stop_monitor
trap - EXIT
ros2 run ee616_evaluation summarize_warehouse_mission "${output_dir}"
ros2 run ee616_evaluation plot_warehouse_mission "${output_dir}"
sha256sum "${output_dir}"/*.json "${output_dir}"/*.csv \
  >"${output_dir}/SHA256SUMS"
