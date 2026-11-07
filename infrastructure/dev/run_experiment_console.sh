#!/usr/bin/env bash
set -eo pipefail

workspace=/workspace/work/ros2_ws
console_slot=$((RANDOM % 50))
# Fast DDS domain-derived ports must stay below the UDP port limit. The
# isolated console range is therefore 150--199 rather than an unbounded value.
export ROS_DOMAIN_ID="${EE616_CONSOLE_ROS_DOMAIN_ID:-$((150 + console_slot))}"
export GZ_PARTITION="${EE616_CONSOLE_GZ_PARTITION:-ee616_console_${console_slot}_${RANDOM}}"

source /opt/ros/jazzy/setup.bash
cd "${workspace}"
colcon build --symlink-install --packages-select \
    ee616_simulation ee616_perception ee616_control ee616_evaluation \
    ee616_dashboard
source "${workspace}/install/setup.bash"

echo "EE616_EXPERIMENT_CONSOLE=http://127.0.0.1:8765"
echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID} GZ_PARTITION=${GZ_PARTITION}"
exec ros2 run ee616_dashboard experiment_console
