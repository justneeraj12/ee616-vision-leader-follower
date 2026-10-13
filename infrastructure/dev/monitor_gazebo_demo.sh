#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash
source /workspace/work/ros2_ws/install/setup.bash

cat <<'EOF'
Useful read-only demo inspection commands:

  ros2 topic hz /follower_1/camera/image
  ros2 topic echo /follower_1/control/state
  ros2 topic echo /follower_1/control/estimate
  ros2 topic echo /experiment/event
  ros2 node list

Follower 2 and 3 use the same topic suffixes under /follower_2 and /follower_3.
The recovery demo dashboard displays /camera/disturbed so the synthetic blackout
is visible. None of these inspection commands publishes into control.
EOF

exec bash
