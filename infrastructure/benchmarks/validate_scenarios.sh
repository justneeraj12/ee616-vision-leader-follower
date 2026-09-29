#!/usr/bin/env bash
set -eo pipefail

workspace=/workspace/work/ros2_ws
result_root="${workspace}/results/scenario_validation"
scenarios=(
    camera_calibration
    straight_aisle
    right_angle_turn
    narrow_aisle
    partial_occlusion
)

source /opt/ros/jazzy/setup.bash
if [[ ! -f "${workspace}/install/setup.bash" ]]; then
    bash /workspace/infrastructure/dev/bootstrap_workspace.sh
fi
source "${workspace}/install/setup.bash"
mkdir -p "${result_root}"

launch_pid=""
stop_launch() {
    if [[ -z "${launch_pid}" ]]; then
        return
    fi
    kill -INT -- "-${launch_pid}" 2>/dev/null || true
    for _attempt in $(seq 1 20); do
        if ! kill -0 -- "-${launch_pid}" 2>/dev/null; then
            break
        fi
        sleep 0.2
    done
    kill -KILL -- "-${launch_pid}" 2>/dev/null || true
    wait "${launch_pid}" 2>/dev/null || true
    launch_pid=""
}
    sleep 1
trap stop_launch EXIT INT TERM

for scenario in "${scenarios[@]}"; do
    scenario_dir="${result_root}/${scenario}"
    mkdir -p "${scenario_dir}"
    setsid ros2 launch ee616_simulation scenario_playground.launch.py \
        scenario:="${scenario}" gui:=false \
        >"${scenario_dir}/launch.log" 2>&1 &
    launch_pid=$!

    timeout 30s ros2 run ee616_bringup camera_probe --ros-args \
        -p topic:=/smoke/camera/image \
        -p required_samples:=30 \
        -p output_path:="${scenario_dir}/camera_probe.json"
    stop_launch
    echo "Validated deterministic scenario: ${scenario}"
done

echo "Scenario validation results: ${result_root}"
