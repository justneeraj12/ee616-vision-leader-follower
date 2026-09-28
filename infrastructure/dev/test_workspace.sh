#!/usr/bin/env bash
set -eo pipefail

workspace=/workspace/work/ros2_ws
source /opt/ros/jazzy/setup.bash
source "${workspace}/install/setup.bash"

cd "${workspace}"
colcon test --event-handlers console_direct+
colcon test-result --verbose
