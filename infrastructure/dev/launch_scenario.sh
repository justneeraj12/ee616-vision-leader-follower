#!/usr/bin/env bash
set -eo pipefail

workspace=/workspace/work/ros2_ws
scenario="${1:-straight_aisle}"

if [[ ! "${scenario}" =~ ^[a-z][a-z0-9_]*$ ]]; then
    echo "EE616_TASK_MESSAGE: Invalid scenario name: ${scenario}" >&2
    exit 2
fi

source /opt/ros/jazzy/setup.bash
installed_launch="${workspace}/install/ee616_simulation/share/ee616_simulation/launch/scenario_playground.launch.py"
if [[ ! -f "${workspace}/install/setup.bash" || ! -f "${installed_launch}" ]]; then
    bash /workspace/infrastructure/dev/bootstrap_workspace.sh
fi
source "${workspace}/install/setup.bash"

echo "EE616_PLAYGROUND_STARTING"
setsid ros2 launch ee616_simulation scenario_playground.launch.py \
    scenario:="${scenario}" gui:=true &
launch_pid=$!

cleanup() {
    kill -INT -- "-${launch_pid}" 2>/dev/null || true
    wait "${launch_pid}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

ready=0
for _attempt in $(seq 1 45); do
    if ros2 topic list 2>/dev/null | grep -qx "/smoke/camera/image"; then
        ready=1
        break
    fi
    if ! kill -0 "${launch_pid}" 2>/dev/null; then
        echo "EE616_TASK_MESSAGE: Scenario launch exited before the camera topic appeared." >&2
        exit 1
    fi
    sleep 1
done

if [[ "${ready}" -ne 1 ]]; then
    echo "EE616_TASK_MESSAGE: Timed out waiting for /smoke/camera/image." >&2
    exit 1
fi

echo "EE616_PLAYGROUND_READY"
echo "Scenario ${scenario} is running. Its generated manifest is in work/ros2_ws/log/generated_scenarios."
wait "${launch_pid}"
