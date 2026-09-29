#!/usr/bin/env bash
set -eo pipefail

workspace=/workspace/work/ros2_ws
run_id="$(date -u +%Y%m%dT%H%M%SZ)"
result_dir="${workspace}/results/aws_world_benchmark/${run_id}"
launch_log="${result_dir}/launch.log"
camera_json="${result_dir}/camera_probe.json"
summary_json="${result_dir}/summary.json"

mkdir -p "${result_dir}"
source /opt/ros/jazzy/setup.bash
if [[ ! -f "${workspace}/install/setup.bash" ]]; then
    bash /workspace/infrastructure/dev/bootstrap_workspace.sh
fi
source "${workspace}/install/setup.bash"

setsid ros2 launch ee616_simulation aws_warehouse_benchmark.launch.py gui:=false \
    >"${launch_log}" 2>&1 &
launch_pid=$!

cleanup() {
    kill -INT -- "-${launch_pid}" 2>/dev/null || true
    for _attempt in $(seq 1 20); do
        if ! kill -0 -- "-${launch_pid}" 2>/dev/null; then
            break
        fi
        sleep 0.2
    done
    kill -KILL -- "-${launch_pid}" 2>/dev/null || true
    wait "${launch_pid}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

timeout 45s ros2 run ee616_bringup camera_probe --ros-args \
    -p topic:=/smoke/camera/image \
    -p required_samples:=150 \
    -p output_path:="${camera_json}"

python3 /workspace/infrastructure/benchmarks/benchmark_gazebo.py \
    --stats-topic /world/aws_no_roof_warehouse/stats \
    --duration-seconds 20 \
    --camera-json "${camera_json}" \
    --launch-log "${launch_log}" \
    --output "${summary_json}"

echo "AWS warehouse benchmark result: ${summary_json}"
