"""Launch one controlled-disturbance experiment."""

from __future__ import annotations

import os
from pathlib import Path
import re
import tempfile

from ament_index_python.packages import get_package_share_directory
from ee616_simulation.disturbance_proxy import DISTURBANCE_SCENARIOS
from ee616_simulation.pair_world import render_disturbance_world
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
        return Path(project_root) / "work" / "ros2_ws" / "log" / "generated_disturbance_worlds"
    return Path(tempfile.gettempdir()) / "ee616_generated_disturbance_worlds"


def _configure(context: LaunchContext):
    scenario = LaunchConfiguration("scenario").perform(context)
    follower_count = int(LaunchConfiguration("follower_count").perform(context))
    run_id = LaunchConfiguration("run_id").perform(context)
    output_dir = LaunchConfiguration("output_dir").perform(context)
    if scenario not in DISTURBANCE_SCENARIOS:
        raise ValueError("unsupported disturbance scenario")
    if follower_count not in {1, 3}:
        raise ValueError("follower_count must be 1 or 3")
    if follower_count == 3 and scenario != "combined":
        raise ValueError("the approved three-follower stage uses the combined scenario")
    if not RUN_ID.fullmatch(run_id):
        raise ValueError("run_id must match run_NN")
    target_follower = 1 if follower_count == 1 else 2
    startup_extension_s = 4.0
    duration_s = (46.0 if scenario == "combined" else 24.0) + startup_extension_s
    simulation_share = Path(get_package_share_directory("ee616_simulation"))
    perception_share = Path(get_package_share_directory("ee616_perception"))
    control_share = Path(get_package_share_directory("ee616_control"))
    world_path = render_disturbance_world(scenario, follower_count, _generated_dir())
    actions = [
        ExecuteProcess(cmd=["gz", "sim", "-r", "-s", "-v", "3", str(world_path)], output="screen"),
        Node(
            package="ros_gz_bridge", executable="parameter_bridge", name="disturbance_bridge",
            parameters=[{"config_file": str(simulation_share / "config" / "chain_bridge.yaml")}], output="screen",
        ),
        Node(
            package="ee616_control", executable="leader_route", namespace="leader",
            parameters=[{
                "profile": scenario,
                "settle_s": 4.0 + startup_extension_s,
                "use_sim_time": True,
            }], output="screen",
        ),
    ]
    for index in range(1, follower_count + 1):
        namespace = f"follower_{index}"
        targeted = index == target_follower
        actions.extend([
            Node(
                package="ee616_simulation", executable="disturbance_proxy", namespace=namespace,
                parameters=[{
                    "scenario": scenario,
                    "apply_disturbance": targeted,
                    "publish_event": targeted,
                    "schedule_delay_s": startup_extension_s,
                    "use_sim_time": True,
                }], output="screen",
            ),
            Node(
                package="ee616_perception", executable="yolo_measurement", namespace=namespace,
                parameters=[
                    str(perception_share / "config" / "yolov8n_target_v3.yaml"),
                    {
                        "image_topic": f"/{namespace}/camera/disturbed",
                        "horizontal_fov_rad": 1.2217304764,
                        "target_height_m": 0.90,
                        "use_sim_time": True,
                    },
                ], output="screen",
            ),
            Node(
                package="ee616_control", executable="follower_controller", namespace=namespace,
                parameters=[
                    str(control_share / "config" / "pair_control.yaml"),
                    {"command_topic": "controller_cmd_vel", "use_sim_time": True},
                ], output="screen",
            ),
        ])
    evaluator = Node(
        package="ee616_evaluation", executable="disturbance_gate_evaluator", name="disturbance_gate_evaluator",
        parameters=[{
            "scenario": scenario,
            "follower_count": follower_count,
            "target_follower": target_follower,
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
            on_exit=[EmitEvent(event=Shutdown(reason="disturbance evaluator completed"))],
        )),
    ])
    return actions


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        DeclareLaunchArgument("scenario", default_value="short_occlusion"),
        DeclareLaunchArgument("follower_count", default_value="1"),
        DeclareLaunchArgument("run_id", default_value="run_01"),
        DeclareLaunchArgument("output_dir", default_value="/workspace/work/ros2_ws/results/disturbance_gate"),
        OpaqueFunction(function=_configure),
    ])
