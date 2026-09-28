#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash
set -u
command -v ros2 >/dev/null
command -v gz >/dev/null
ros2 pkg prefix ros_gz_bridge >/dev/null
gz sim --version >/dev/null
