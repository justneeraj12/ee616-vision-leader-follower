"""Launch one learned-vision leader-follower integration run."""

from __future__ import annotations

import os
from pathlib import Path
import re
import tempfile

from ament_index_python.packages import get_package_share_directory
from ee616_simulation.pair_world import PAIR_PROFILES, render_pair_world
from launch import LaunchContext, LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    ExecuteProcess,
    OpaqueFunction,
    RegisterEventHandler,
    TimerAction,
)
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


def _as_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError("gui must be true or false")
    return normalized == "true"


def _configure(context: LaunchContext):
    profile = LaunchConfiguration("profile").perform(context)
    run_id = LaunchConfiguration("run_id").perform(context)
    output_dir = LaunchConfiguration("output_dir").perform(context)
    gui = _as_bool(LaunchConfiguration("gui").perform(context))
    render_engine = LaunchConfiguration("render_engine").perform(context)
    detector_device = LaunchConfiguration("detector_device").perform(context)
    startup_extension_s = float(
        LaunchConfiguration("startup_extension_s").perform(context)
    )
    if not 0.0 <= startup_extension_s <= 30.0:
        raise ValueError("startup_extension_s must be between 0 and 30")
    if profile not in PAIR_PROFILES:
        raise ValueError("profile must be straight or turn")
    if render_engine not in {"ogre", "ogre2"}:
        raise ValueError("render_engine must be ogre or ogre2")
    if not RUN_ID.fullmatch(run_id):
        raise ValueError("run_id must match run_NN")
    simulation_share = Path(get_package_share_directory("ee616_simulation"))
    perception_share = Path(get_package_share_directory("ee616_perception"))
    control_share = Path(get_package_share_directory("ee616_control"))
    world_path = render_pair_world(profile, _generated_dir())
    duration_s = (24.0 if profile == "straight" else 26.0) + startup_extension_s
    simulation_command = [
        "gz", "sim", "-s", "-r", "-v", "3",
        "--render-engine-server", render_engine,
        str(world_path),
    ]
    simulation = ExecuteProcess(
        cmd=simulation_command,
        additional_env={"EGL_PLATFORM": "surfaceless"},
        output="screen",
    )
    actions = [simulation]
    if gui:
        actions.append(
            TimerAction(
                period=2.0,
                actions=[ExecuteProcess(
                    cmd=[
                        "gz", "sim", "-g", "-v", "3",
                        "--render-engine-gui", render_engine,
                    ],
                    output="screen",
                )],
            )
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
        parameters=[{
            "profile": profile,
            "settle_s": 4.0 + startup_extension_s,
            "use_sim_time": True,
        }],
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
                "device": detector_device,
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
                "warmup_s": 4.0 + startup_extension_s,
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
    actions.extend([bridge, leader, perception, follower, evaluator, shutdown])
    return actions


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument("profile", default_value="straight"),
            DeclareLaunchArgument("run_id", default_value="run_01"),
            DeclareLaunchArgument("gui", default_value="false"),
            DeclareLaunchArgument("render_engine", default_value="ogre2"),
            DeclareLaunchArgument("detector_device", default_value="0"),
            DeclareLaunchArgument("startup_extension_s", default_value="0.0"),
            DeclareLaunchArgument(
                "output_dir",
                default_value="/workspace/work/ros2_ws/results/pair_gate",
            ),
            OpaqueFunction(function=_configure),
        ]
    )
