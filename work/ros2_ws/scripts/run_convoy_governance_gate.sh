#!/usr/bin/env bash
set -euo pipefail

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${workspace_dir}/results/convoy_governance_evidence"
stop_file=/tmp/ee616-convoy-governance-stop

export ROS_DOMAIN_ID=176
export GZ_PARTITION="ee616_convoy_governance_${BASHPID}"
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select \
  ee616_simulation ee616_perception ee616_control ee616_evaluation
source "${workspace_dir}/install/setup.bash"

if [[ -d "${output_dir}" ]] \
  && find "${output_dir}" -mindepth 1 -print -quit | grep -q .; then
  echo "Move the existing completion evidence before repeating this matrix." >&2
  exit 2
fi
mkdir -p "${output_dir}"
rm -f "${stop_file}"
python3 "${workspace_dir}/scripts/component_resource_monitor.py" \
  --stop-file "${stop_file}" \
  --samples-output "${output_dir}/component_resources.csv" \
  --summary-output "${output_dir}/component_resources.json" &
monitor_pid=$!
cleanup() {
  touch "${stop_file}"
  wait "${monitor_pid}" || true
}
trap cleanup EXIT

run_profile() {
  local followers=$1 map=$2 route=$3 scenario=$4 repetition=$5 duration=$6
  local profile_dir="${output_dir}/${map}_${route}_${scenario}_${followers}f"
  mkdir -p "${profile_dir}"
  local fault_mode=none require_fault=false
  if [[ "${scenario}" == leader_dropout ]]; then
    fault_mode=leader_cmd_dropout
    require_fault=true
  fi
  ros2 launch ee616_evaluation warehouse_nav_mission.launch.py \
    follower_count:="${followers}" map_profile:="${map}" \
    route_profile:="${route}" fault_mode:="${fault_mode}" \
    require_fault_event:="${require_fault}" \
    minimum_track_fraction:=0.85 max_f1_rmse_m:=0.30 \
    max_later_rmse_m:=0.35 run_id:="run_${repetition}" \
    output_dir:="${profile_dir}" duration_s:="${duration}" gui:=false
}

echo "Stage 1/3: repeat the sparse-layout nominal pair."
for repetition in 01 02 03; do
  run_profile 1 sparse wide nominal "${repetition}" 460.0
done

echo "Stage 2/3: repeat three-follower visual-loss containment."
for repetition in 01 02 03; do
  run_profile 3 sparse wide containment "${repetition}" 520.0
done

echo "Stage 3/3: repeat bounded leader command-dropout recovery."
for repetition in 01 02 03; do
  run_profile 1 sparse wide leader_dropout "${repetition}" 480.0
done

cleanup
trap - EXIT
python3 "${workspace_dir}/scripts/verify_convoy_governance_gate.py" \
  "${output_dir}"
(
  cd "${output_dir}"
  find . -type f \( -name '*.json' -o -name '*.csv' -o -name 'README.md' \) -print0 \
    | sort -z | xargs -0 sha256sum >SHA256SUMS
)
echo "Convoy-governance evidence: ${output_dir}"
