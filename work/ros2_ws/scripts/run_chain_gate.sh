#!/usr/bin/env bash
set -eo pipefail

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${workspace_dir}/results/chain_gate"
stop_file=/tmp/ee616-chain-gate-stop
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

for profile in straight turn; do
  for repetition in 01 02 03; do
    ros2 launch ee616_evaluation chain_gate.launch.py \
      profile:="${profile}" follower_count:=2 run_id:="run_${repetition}" output_dir:="${output_dir}"
  done
done

# Scientific staging rule: Follower 3 is not launched until the two-follower stage passes.
ros2 run ee616_evaluation summarize_chain_gate "${output_dir}" --max-followers 2

for profile in straight turn; do
  for repetition in 01 02 03; do
    ros2 launch ee616_evaluation chain_gate.launch.py \
      profile:="${profile}" follower_count:=3 run_id:="run_${repetition}" output_dir:="${output_dir}"
  done
done

stop_monitor
trap - EXIT
ros2 run ee616_evaluation summarize_chain_gate "${output_dir}" --max-followers 3
ros2 run ee616_evaluation plot_chain_gate "${output_dir}"
