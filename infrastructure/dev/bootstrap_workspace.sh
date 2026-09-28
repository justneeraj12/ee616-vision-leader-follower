#!/usr/bin/env bash
set -eo pipefail

workspace=/workspace/work/ros2_ws
source /opt/ros/jazzy/setup.bash

cd "${workspace}"
colcon build --symlink-install --event-handlers console_direct+

echo "ROS 2 workspace built. Open a new terminal or source ${workspace}/install/setup.bash."
