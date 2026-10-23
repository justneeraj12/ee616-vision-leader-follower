#!/usr/bin/env bash
set -eo pipefail

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${workspace_dir}/results/warehouse_nav_evidence"
stop_file=/tmp/ee616-warehouse-nav-mission-stop
resource_output="${output_dir}/resources.json"
resource_samples="${output_dir}/resource_samples.csv"

# Keep evidence runs isolated from an open GUI demo or an interrupted shell.
export ROS_DOMAIN_ID=157
export GZ_PARTITION="ee616_warehouse_nav_${BASHPID}"

source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select \
  ee616_simulation ee616_perception ee616_control ee616_evaluation
source "${workspace_dir}/install/setup.bash"

mkdir -p "${output_dir}"
if compgen -G "${output_dir}/warehouse_mission_*_summary.json" >/dev/null; then
  echo "Evidence directory already contains run summaries: ${output_dir}" >&2
  echo "Move or archive them before starting another frozen evidence set." >&2
  exit 2
fi

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

echo "Stage 1/2: validating the minimum scientific unit (leader + follower)."
ros2 launch ee616_evaluation warehouse_nav_mission.launch.py \
  follower_count:=1 run_id:=run_01 output_dir:="${output_dir}"
ros2 run ee616_evaluation summarize_warehouse_mission \
  "${output_dir}" --max-followers 1

echo "Stage 2/2: running three independent one-leader/three-follower trials."
for repetition in 01 02 03; do
  ros2 launch ee616_evaluation warehouse_nav_mission.launch.py \
    follower_count:=3 run_id:="run_${repetition}" output_dir:="${output_dir}"
done

stop_monitor
trap - EXIT
ros2 run ee616_evaluation summarize_warehouse_mission "${output_dir}"
ros2 run ee616_evaluation plot_warehouse_mission "${output_dir}"
sha256sum "${output_dir}"/*.json "${output_dir}"/*.csv \
  >"${output_dir}/SHA256SUMS"

echo "Verified evidence: ${output_dir}/summary.json"
