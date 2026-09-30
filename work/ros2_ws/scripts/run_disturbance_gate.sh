#!/usr/bin/env bash
set -eo pipefail

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${workspace_dir}/results/disturbance_gate"
stop_file=/tmp/ee616-disturbance-gate-stop
resource_output="${output_dir}/resources.json"

source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source "${workspace_dir}/install/setup.bash"

mkdir -p "${output_dir}"
rm -f "${stop_file}"
python3 "${workspace_dir}/scripts/resource_monitor.py" \
  --stop-file "${stop_file}" --output "${resource_output}" --interval 0.5 &
monitor_pid=$!

stop_monitor() {
  touch "${stop_file}"
  wait "${monitor_pid}" || true
}
trap stop_monitor EXIT

for scenario in sharp_turn short_occlusion long_occlusion leader_stop actuator_bias; do
  for repetition in 01 02 03; do
    ros2 launch ee616_evaluation disturbance_gate.launch.py \
      scenario:="${scenario}" follower_count:=1 run_id:="run_${repetition}" output_dir:="${output_dir}"
  done
done

# Gate 5 remains pair-first: no chain disturbance may run until all 15 pair runs pass.
ros2 run ee616_evaluation summarize_disturbance_gate "${output_dir}" --stage pair

for repetition in 01 02 03; do
  ros2 launch ee616_evaluation disturbance_gate.launch.py \
    scenario:=combined follower_count:=3 run_id:="run_${repetition}" output_dir:="${output_dir}"
done

stop_monitor
trap - EXIT
ros2 run ee616_evaluation summarize_disturbance_gate "${output_dir}" --stage full
ros2 run ee616_evaluation plot_disturbance_gate "${output_dir}"
