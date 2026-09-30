"""Launch one isolated Gazebo scene and its offline dataset recorder."""

from __future__ import annotations

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from ee616_simulation.scenario_builder import load_scenario
from launch import LaunchContext, LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    IncludeLaunchDescription,
    OpaqueFunction,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _configure(context: LaunchContext):
    scene = LaunchConfiguration("scene").perform(context)
    split = LaunchConfiguration("split").perform(context)
    output_dir = LaunchConfiguration("output_dir").perform(context)
    start_condition_index = int(
        LaunchConfiguration("start_condition_index").perform(context)
    )
    capture_config = LaunchConfiguration("capture_config").perform(context)
    if capture_config not in {
        "yolo_dataset_capture.yaml",
        "yolo_dataset_capture_v2.yaml",
        "yolo_dataset_capture_v3.yaml",
        "yolo_failure_diagnostic.yaml",
    }:
        raise ValueError(f"unsupported capture config: {capture_config}")
    simulation_share = Path(get_package_share_directory("ee616_simulation"))
    evaluation_share = Path(get_package_share_directory("ee616_evaluation"))
    scenario, _ = load_scenario(
        simulation_share / "scenarios" / f"{scene}.yaml"
    )
    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(simulation_share / "launch" / "scenario_playground.launch.py")
        ),
        launch_arguments={"scenario": scene, "gui": "false"}.items(),
    )
    recorder = Node(
        package="ee616_evaluation",
        executable="yolo_dataset_capture",
        name="yolo_dataset_capture",
        parameters=[
            str(evaluation_share / "config" / capture_config),
            {
                "scene": scene,
                "split": split,
                "output_dir": output_dir,
                "start_condition_index": start_condition_index,
                "horizontal_fov_rad": scenario["camera"]["horizontal_fov_rad"],
                "image_width": scenario["camera"]["width"],
                "image_height": scenario["camera"]["height"],
                "target_size": scenario["target"]["size"],
                "target_z": scenario["target"]["pose"][2],
                "target_yaw": scenario["target"]["pose"][5],
            },
        ],
        output="screen",
    )
    shutdown = RegisterEventHandler(
        OnProcessExit(
            target_action=recorder,
            on_exit=[
                EmitEvent(
                    event=Shutdown(reason="YOLO dataset scene completed")
                )
            ],
        )
    )
    return [simulation, recorder, shutdown]


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument("scene", default_value="yolo_train_open"),
            DeclareLaunchArgument("split", default_value="train"),
            DeclareLaunchArgument(
                "start_condition_index",
                default_value="0",
            ),
            DeclareLaunchArgument(
                "capture_config",
                default_value="yolo_dataset_capture.yaml",
            ),
            DeclareLaunchArgument(
                "output_dir",
                default_value=(
                    "/workspace/work/ros2_ws/datasets/"
                    "ee616_predecessor_target_v1"
                ),
            ),
            OpaqueFunction(function=_configure),
        ]
    )
