#!/usr/bin/env bash
set -eo pipefail

workspace=/workspace/work/ros2_ws
source /opt/ros/jazzy/setup.bash

installed_launch="${workspace}/install/ee616_simulation/share/ee616_simulation/launch/aws_warehouse_benchmark.launch.py"
if [[ ! -f "${workspace}/install/setup.bash" || ! -f "${installed_launch}" ]]; then
    bash /workspace/infrastructure/dev/bootstrap_workspace.sh
fi
source "${workspace}/install/setup.bash"

echo "EE616_AWS_WAREHOUSE_STARTING"
setsid ros2 launch ee616_simulation aws_warehouse_benchmark.launch.py gui:=true &
launch_pid=$!

cleanup() {
    kill -INT -- "-${launch_pid}" 2>/dev/null || true
    wait "${launch_pid}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

ready=0
for _attempt in $(seq 1 60); do
    if ros2 topic list 2>/dev/null | grep -qx "/smoke/camera/image"; then
        ready=1
        break
    fi
    if ! kill -0 "${launch_pid}" 2>/dev/null; then
        echo "EE616_TASK_MESSAGE: AWS warehouse launch exited before the camera topic appeared." >&2
        exit 1
    fi
    sleep 1
done

if [[ "${ready}" -ne 1 ]]; then
    echo "EE616_TASK_MESSAGE: Timed out waiting for the AWS warehouse camera topic." >&2
    exit 1
fi

echo "EE616_AWS_WAREHOUSE_READY"
echo "AWS no-roof warehouse is running as an optional visual stress test."
wait "${launch_pid}"
