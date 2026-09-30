#!/usr/bin/env bash
set -eo pipefail

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${workspace_dir}/results/pair_gate"
stop_file=/tmp/ee616-pair-gate-stop
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

for profile in straight turn; do
  for repetition in 01 02 03; do
    ros2 launch ee616_evaluation pair_gate.launch.py \
      profile:="${profile}" run_id:="run_${repetition}" output_dir:="${output_dir}"
  done
done

ros2 run ee616_evaluation summarize_pair_gate "${output_dir}"
ros2 run ee616_evaluation plot_pair_gate "${output_dir}"
