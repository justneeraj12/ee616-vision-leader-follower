"""Launch one incremental learned-vision convoy run."""

from __future__ import annotations

import os
from pathlib import Path
import re
import tempfile

from ament_index_python.packages import get_package_share_directory
from ee616_simulation.pair_world import PAIR_PROFILES, render_chain_world
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
        return Path(project_root) / "work" / "ros2_ws" / "log" / "generated_chain_worlds"
    return Path(tempfile.gettempdir()) / "ee616_generated_chain_worlds"


def _as_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError("gui must be true or false")
    return normalized == "true"


def _configure(context: LaunchContext):
    profile = LaunchConfiguration("profile").perform(context)
    follower_count = int(LaunchConfiguration("follower_count").perform(context))
    run_id = LaunchConfiguration("run_id").perform(context)
    output_dir = LaunchConfiguration("output_dir").perform(context)
    gui = _as_bool(LaunchConfiguration("gui").perform(context))
    startup_extension_s = float(
        LaunchConfiguration("startup_extension_s").perform(context)
    )
    if not 0.0 <= startup_extension_s <= 30.0:
        raise ValueError("startup_extension_s must be between 0 and 30")
    if profile not in PAIR_PROFILES:
        raise ValueError("profile must be straight or turn")
    if follower_count not in {2, 3}:
        raise ValueError("follower_count must be 2 or 3")
    if not RUN_ID.fullmatch(run_id):
        raise ValueError("run_id must match run_NN")
    simulation_share = Path(get_package_share_directory("ee616_simulation"))
    perception_share = Path(get_package_share_directory("ee616_perception"))
    control_share = Path(get_package_share_directory("ee616_control"))
    world_path = render_chain_world(profile, follower_count, _generated_dir())
    duration_s = (24.0 if profile == "straight" else 26.0) + startup_extension_s
    simulation_command = ["gz", "sim", "-r"]
    if not gui:
        simulation_command.append("-s")
    simulation_command.extend(["-v", "3", str(world_path)])
    actions = [
        ExecuteProcess(cmd=simulation_command, output="screen"),
        Node(
            package="ros_gz_bridge", executable="parameter_bridge", name="chain_bridge",
            parameters=[{"config_file": str(simulation_share / "config" / "chain_bridge.yaml")}],
            output="screen",
        ),
        Node(
            package="ee616_control", executable="leader_route", namespace="leader",
            parameters=[{
                "profile": profile,
                "settle_s": 4.0 + startup_extension_s,
                "use_sim_time": True,
            }], output="screen",
        ),
    ]
    for index in range(1, follower_count + 1):
        namespace = f"follower_{index}"
        actions.extend([
            Node(
                package="ee616_perception", executable="yolo_measurement", namespace=namespace,
                parameters=[
                    str(perception_share / "config" / "yolov8n_target_v3.yaml"),
                    {
                        "image_topic": f"/{namespace}/camera/image",
                        "horizontal_fov_rad": 1.2217304764,
                        "target_height_m": 0.90,
                        "use_sim_time": True,
                    },
                ], output="screen",
            ),
            Node(
                package="ee616_control", executable="follower_controller", namespace=namespace,
                parameters=[str(control_share / "config" / "pair_control.yaml"), {"use_sim_time": True}],
                output="screen",
            ),
        ])
    evaluator = Node(
        package="ee616_evaluation", executable="chain_gate_evaluator", name="chain_gate_evaluator",
        parameters=[{
            "profile": profile,
            "follower_count": follower_count,
            "run_id": run_id,
            "output_dir": output_dir,
            "duration_s": duration_s,
            "warmup_s": 4.0 + startup_extension_s,
            "use_sim_time": True,
        }], output="screen",
    )
    actions.extend([
        evaluator,
        RegisterEventHandler(OnProcessExit(
            target_action=evaluator,
            on_exit=[EmitEvent(event=Shutdown(reason="chain evaluator completed"))],
        )),
    ])
    return actions


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        DeclareLaunchArgument("profile", default_value="straight"),
        DeclareLaunchArgument("follower_count", default_value="2"),
        DeclareLaunchArgument("run_id", default_value="run_01"),
        DeclareLaunchArgument("gui", default_value="false"),
        DeclareLaunchArgument("startup_extension_s", default_value="0.0"),
        DeclareLaunchArgument("output_dir", default_value="/workspace/work/ros2_ws/results/chain_gate"),
        OpaqueFunction(function=_configure),
    ])
