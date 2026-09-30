#!/usr/bin/env bash
set -eo pipefail

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${workspace_dir}/results/timing_gate"
stop_file=/tmp/ee616-timing-gate-stop
resource_output="${output_dir}/resources.json"
resource_samples="${output_dir}/resource_samples.csv"

source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source "${workspace_dir}/install/setup.bash"

mkdir -p "${output_dir}"
rm -f "${stop_file}"
python3 "${workspace_dir}/scripts/resource_monitor.py" \
  --stop-file "${stop_file}" \
  --output "${resource_output}" \
  --samples-output "${resource_samples}" \
  --interval 0.25 &
monitor_pid=$!

stop_monitor() {
  touch "${stop_file}"
  wait "${monitor_pid}" || true
}
trap stop_monitor EXIT

for repetition in 01 02 03; do
  ros2 launch ee616_evaluation timing_gate.launch.py \
    run_id:="run_${repetition}" output_dir:="${output_dir}"
done

stop_monitor
trap - EXIT
ros2 run ee616_evaluation summarize_timing_gate "${output_dir}"
ros2 run ee616_evaluation plot_timing_gate "${output_dir}"
