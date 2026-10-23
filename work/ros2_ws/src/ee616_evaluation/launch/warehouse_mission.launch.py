"""Launch one optimized pair-first or full warehouse cargo mission."""

from __future__ import annotations

import os
from pathlib import Path
import re
import tempfile

from ament_index_python.packages import get_package_share_directory
from ee616_control.warehouse_mission import WarehouseMissionPlan
from ee616_simulation.warehouse_mission_world import render_warehouse_mission_world
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
        return Path(project_root) / "work" / "ros2_ws" / "log" / "generated_mission_worlds"
    return Path(tempfile.gettempdir()) / "ee616_generated_mission_worlds"


def _as_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError("gui must be true or false")
    return normalized == "true"


def _configure(context: LaunchContext):
    follower_count = int(LaunchConfiguration("follower_count").perform(context))
    run_id = LaunchConfiguration("run_id").perform(context)
    output_dir = LaunchConfiguration("output_dir").perform(context)
    gui = _as_bool(LaunchConfiguration("gui").perform(context))
    render_engine = LaunchConfiguration("render_engine").perform(context)
    detector_device = LaunchConfiguration("detector_device").perform(context)
    startup_s = float(LaunchConfiguration("startup_s").perform(context))
    if follower_count not in {1, 3}:
        raise ValueError("follower_count must be 1 or 3")
    if not RUN_ID.fullmatch(run_id):
        raise ValueError("run_id must match run_NN")
    if render_engine not in {"ogre", "ogre2"}:
        raise ValueError("render_engine must be ogre or ogre2")
    if not 0.0 <= startup_s <= 30.0:
        raise ValueError("startup_s must be between 0 and 30")

    simulation_share = Path(get_package_share_directory("ee616_simulation"))
    perception_share = Path(get_package_share_directory("ee616_perception"))
    control_share = Path(get_package_share_directory("ee616_control"))
    world_path = render_warehouse_mission_world(follower_count, _generated_dir())
    mission = WarehouseMissionPlan(follower_count, startup_s=startup_s)
    duration_s = mission.total_duration_s + 3.0
    model_path = simulation_share / "vendor" / "aws_small_warehouse" / "models"
    existing_path = os.environ.get("GZ_SIM_RESOURCE_PATH", "")
    resource_path = f"{model_path}:{existing_path}" if existing_path else str(model_path)
    common_env = {
        "EGL_PLATFORM": "surfaceless",
        "GZ_SIM_RESOURCE_PATH": resource_path,
    }
    actions = [
        ExecuteProcess(
            cmd=[
                "gz", "sim", "-s", "-r", "-v", "3",
                "--render-engine-server", render_engine, str(world_path),
            ],
            additional_env=common_env,
            output="screen",
        ),
        Node(
            package="ros_gz_bridge", executable="parameter_bridge",
            name="warehouse_mission_bridge",
            parameters=[{
                "config_file": str(
                    simulation_share / "config" / "warehouse_mission_bridge.yaml"
                )
            }],
            output="screen",
        ),
        Node(
            package="ee616_control", executable="warehouse_mission",
            namespace="leader",
            parameters=[{
                "follower_count": follower_count,
                "startup_s": startup_s,
                "use_sim_time": True,
            }],
            output="screen",
        ),
    ]
    if gui:
        actions.insert(
            1,
            TimerAction(
                period=2.0,
                actions=[ExecuteProcess(
                    cmd=[
                        "gz", "sim", "-g", "-v", "3",
                        "--render-engine-gui", render_engine,
                    ],
                    additional_env={"GZ_SIM_RESOURCE_PATH": resource_path},
                    output="screen",
                )],
            ),
        )
    for index in range(1, follower_count + 1):
        namespace = f"follower_{index}"
        actions.extend([
            Node(
                package="ee616_perception", executable="yolo_measurement",
                namespace=namespace,
                parameters=[
                    str(perception_share / "config" / "yolov8n_target_v3.yaml"),
                    {
                        "image_topic": f"/{namespace}/camera/image",
                        "horizontal_fov_rad": 1.2217304764,
                        "target_height_m": 0.90,
                        "device": detector_device,
                        "use_sim_time": True,
                    },
                ],
                output="screen",
            ),
            Node(
                package="ee616_control", executable="follower_controller",
                namespace=namespace,
                parameters=[
                    str(control_share / "config" / "pair_control.yaml"),
                    {"use_sim_time": True},
                ],
                output="screen",
            ),
        ])
    evaluator = Node(
        package="ee616_evaluation", executable="warehouse_mission_evaluator",
        name="warehouse_mission_evaluator",
        parameters=[{
            "follower_count": follower_count,
            "run_id": run_id,
            "output_dir": output_dir,
            "duration_s": duration_s,
            "use_sim_time": True,
        }],
        output="screen",
    )
    actions.extend([
        evaluator,
        RegisterEventHandler(OnProcessExit(
            target_action=evaluator,
            on_exit=[EmitEvent(event=Shutdown(reason="warehouse evaluator completed"))],
        )),
    ])
    return actions


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        DeclareLaunchArgument("follower_count", default_value="3"),
        DeclareLaunchArgument("run_id", default_value="run_01"),
        DeclareLaunchArgument("gui", default_value="false"),
        DeclareLaunchArgument("render_engine", default_value="ogre2"),
        DeclareLaunchArgument("detector_device", default_value="0"),
        DeclareLaunchArgument("startup_s", default_value="10.0"),
        DeclareLaunchArgument(
            "output_dir",
            default_value="/workspace/work/ros2_ws/results/warehouse_mission",
        ),
        OpaqueFunction(function=_configure),
    ])
