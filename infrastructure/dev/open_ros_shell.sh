#!/usr/bin/env bash
set -eo pipefail

workspace=/workspace/work/ros2_ws
source /opt/ros/jazzy/setup.bash

if [[ -f "${workspace}/install/setup.bash" ]]; then
    source "${workspace}/install/setup.bash"
fi

echo "EE 616 ROS learning shell"
echo "Try: ros2 node list"
echo "Try: ros2 topic list"
echo "Try: ros2 topic hz /smoke/camera/image"
echo "Try: gz topic -l"

export PS1='[EE616 ROS2] \w \$ '
exec bash --noprofile --norc
