#!/usr/bin/env bash
set -eo pipefail

mode="${1:-pair_turn}"
case "${mode}" in
    pair_turn|chain_straight|chain_turn|recovery|warehouse_mission|warehouse_nav_mission) ;;
    *)
        echo "Usage: $0 {pair_turn|chain_straight|chain_turn|recovery|warehouse_mission|warehouse_nav_mission}" >&2
        exit 2
        ;;
esac

workspace=/workspace/work/ros2_ws
demo_slot=$((RANDOM % 100))
export ROS_DOMAIN_ID="${EE616_DEMO_ROS_DOMAIN_ID:-$((100 + demo_slot))}"
export GZ_PARTITION="${EE616_DEMO_GZ_PARTITION:-ee616_demo_${demo_slot}_${RANDOM}}"
source /opt/ros/jazzy/setup.bash
cd "${workspace}"

colcon build --symlink-install --packages-select \
    ee616_simulation ee616_perception ee616_control ee616_evaluation
source "${workspace}/install/setup.bash"

echo "EE616_DEMO_STARTING mode=${mode}"
echo "EE616_DEMO_ISOLATION ros_domain=${ROS_DOMAIN_ID} gz_partition=${GZ_PARTITION}"
echo "The Gazebo and camera-dashboard windows are read-only presentation views."
echo "Results are written below results/demo_runs, never into frozen gate directories."
ros2 launch ee616_evaluation gazebo_demo.launch.py mode:="${mode}"
