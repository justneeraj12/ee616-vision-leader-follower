"""Launch one learned-vision leader-follower integration run."""

from __future__ import annotations

import os
from pathlib import Path
import re
import tempfile

from ament_index_python.packages import get_package_share_directory
from ee616_simulation.pair_world import PAIR_PROFILES, render_pair_world
from launch import LaunchContext, LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, ExecuteProcess, OpaqueFunction, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


RUN_ID = re.compile(r"^run_[0-9]{2}$")


def _generated_dir() -> Path:
    project_root = os.environ.get("EE616_PROJECT_ROOT")
    if project_root:
        return Path(project_root) / "work" / "ros2_ws" / "log" / "generated_pair_worlds"
    return Path(tempfile.gettempdir()) / "ee616_generated_pair_worlds"


def _configure(context: LaunchContext):
    profile = LaunchConfiguration("profile").perform(context)
    run_id = LaunchConfiguration("run_id").perform(context)
    output_dir = LaunchConfiguration("output_dir").perform(context)
    if profile not in PAIR_PROFILES:
        raise ValueError("profile must be straight or turn")
    if not RUN_ID.fullmatch(run_id):
        raise ValueError("run_id must match run_NN")
    simulation_share = Path(get_package_share_directory("ee616_simulation"))
    perception_share = Path(get_package_share_directory("ee616_perception"))
    control_share = Path(get_package_share_directory("ee616_control"))
    world_path = render_pair_world(profile, _generated_dir())
    duration_s = 24.0 if profile == "straight" else 26.0
    simulation = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-s", "-v", "3", str(world_path)],
        output="screen",
    )
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="pair_bridge",
        parameters=[{"config_file": str(simulation_share / "config" / "pair_bridge.yaml")}],
        output="screen",
    )
    leader = Node(
        package="ee616_control",
        executable="leader_route",
        namespace="leader",
        parameters=[{"profile": profile, "use_sim_time": True}],
        output="screen",
    )
    perception = Node(
        package="ee616_perception",
        executable="yolo_measurement",
        namespace="follower_1",
        parameters=[
            str(perception_share / "config" / "yolov8n_target_v3.yaml"),
            {
                "image_topic": "/follower_1/camera/image",
                "horizontal_fov_rad": 1.2217304764,
                "target_height_m": 0.90,
                "use_sim_time": True,
            },
        ],
        output="screen",
    )
    follower = Node(
        package="ee616_control",
        executable="follower_controller",
        namespace="follower_1",
        parameters=[
            str(control_share / "config" / "pair_control.yaml"),
            {"use_sim_time": True},
        ],
        output="screen",
    )
    evaluator = Node(
        package="ee616_evaluation",
        executable="pair_gate_evaluator",
        name="pair_gate_evaluator",
        parameters=[
            {
                "profile": profile,
                "run_id": run_id,
                "output_dir": output_dir,
                "duration_s": duration_s,
                "use_sim_time": True,
            }
        ],
        output="screen",
    )
    shutdown = RegisterEventHandler(
        OnProcessExit(
            target_action=evaluator,
            on_exit=[EmitEvent(event=Shutdown(reason="pair evaluator completed"))],
        )
    )
    return [simulation, bridge, leader, perception, follower, evaluator, shutdown]


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument("profile", default_value="straight"),
            DeclareLaunchArgument("run_id", default_value="run_01"),
            DeclareLaunchArgument(
                "output_dir",
                default_value="/workspace/work/ros2_ws/results/pair_gate",
            ),
            OpaqueFunction(function=_configure),
        ]
    )
