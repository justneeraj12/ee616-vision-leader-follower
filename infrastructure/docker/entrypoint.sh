#!/usr/bin/env bash
set -e

source /opt/ros/jazzy/setup.bash

if [[ -f /workspace/work/ros2_ws/install/setup.bash ]]; then
    source /workspace/work/ros2_ws/install/setup.bash
fi

exec "$@"
