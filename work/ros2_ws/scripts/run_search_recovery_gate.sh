#!/usr/bin/env bash
set -eo pipefail

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${workspace_dir}/results/search_recovery_evidence"
stop_file=/tmp/ee616-search-recovery-stop

export ROS_DOMAIN_ID=177
export GZ_PARTITION="ee616_search_recovery_${BASHPID}"
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select \
  ee616_simulation ee616_perception ee616_control ee616_evaluation
source "${workspace_dir}/install/setup.bash"
set -u

if [[ -d "${output_dir}" ]] \
  && find "${output_dir}" -mindepth 1 -print -quit | grep -q .; then
  echo "Move the existing search-recovery evidence before repeating this matrix." >&2
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
  local followers=$1 scenario=$2 repetition=$3
  local profile_dir="${output_dir}/sparse_wide_${scenario}_${followers}f"
  mkdir -p "${profile_dir}"
  local fault_mode=none require_fault=false
  if [[ "${scenario}" == leader_dropout ]]; then
    fault_mode=leader_cmd_dropout
    require_fault=true
  fi
  ros2 launch ee616_evaluation warehouse_nav_mission.launch.py \
    follower_count:="${followers}" map_profile:=sparse route_profile:=wide \
    fault_mode:="${fault_mode}" require_fault_event:="${require_fault}" \
    run_id:="run_${repetition}" output_dir:="${profile_dir}" \
    duration_s:=320.0 gui:=false render_engine:=ogre2 detector_device:=0 \
    startup_s:=12.0
  python3 - "${profile_dir}" "${repetition}" <<'PY'
import json
import sys
from pathlib import Path

profile_dir = Path(sys.argv[1])
repetition = sys.argv[2]
paths = sorted(profile_dir.glob(f"*_run_{repetition}_summary.json"))
if len(paths) != 1:
    raise SystemExit(f"expected one summary for run_{repetition}, got {len(paths)}")
summary = json.loads(paths[0].read_text(encoding="utf-8"))
if not summary.get("mission_checks", {}).get("route_complete", False):
    raise SystemExit(f"route did not complete in {paths[0]}")
PY
}

echo "Stage 0/3: force one controlled pair visual loss through SEARCH recovery."
mkdir -p "${output_dir}/pair_visual_blackout"
ros2 launch ee616_evaluation disturbance_gate.launch.py \
  scenario:=long_occlusion follower_count:=1 search_enabled:=true \
  run_id:=run_01 output_dir:="${output_dir}/pair_visual_blackout" \
  gui:=false render_engine:=ogre2 detector_device:=0 startup_extension_s:=4.0

echo "Stage 1/3: repeat the validated nominal pair."
for repetition in 01 02 03; do
  run_profile 1 nominal "${repetition}"
done

echo "Stage 2/3: repeat the nominal three-follower chain."
for repetition in 01 02 03; do
  run_profile 3 nominal "${repetition}"
done

echo "Stage 3/3: repeat three-follower leader command-dropout recovery."
for repetition in 01 02 03; do
  run_profile 3 leader_dropout "${repetition}"
done

cleanup
trap - EXIT
python3 "${workspace_dir}/scripts/verify_search_recovery_gate.py" \
  "${output_dir}"
(
  cd "${output_dir}"
  find . -type f \( -name '*.json' -o -name '*.csv' -o -name 'README.md' \) -print0 \
    | sort -z | xargs -0 sha256sum >SHA256SUMS
)
echo "Search-recovery evidence: ${output_dir}"
