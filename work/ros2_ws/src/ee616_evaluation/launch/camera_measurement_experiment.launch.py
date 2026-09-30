"""Run one camera-only measurement scene with an isolated evaluator."""

from __future__ import annotations

import json
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
    output_dir = LaunchConfiguration("output_dir").perform(context)
    detector = LaunchConfiguration("detector").perform(context)
    yolo_config = LaunchConfiguration("yolo_config").perform(context)
    simulation_share = Path(get_package_share_directory("ee616_simulation"))
    perception_share = Path(get_package_share_directory("ee616_perception"))
    scenario_path = simulation_share / "scenarios" / f"{scene}.yaml"
    scenario, _ = load_scenario(scenario_path)

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(simulation_share / "launch" / "scenario_playground.launch.py")
        ),
        launch_arguments={"scenario": scene, "gui": "false"}.items(),
    )
    if detector == "red_baseline":
        executable = "camera_measurement"
        config_name = "red_target_baseline.yaml"
        evaluator_overrides = {}
    elif detector == "yolov8n":
        executable = "yolo_measurement"
        if yolo_config not in {
            "yolov8n_target.yaml",
            "yolov8n_target_v2.yaml",
            "yolov8n_target_v3.yaml",
        }:
            raise ValueError(f"unsupported YOLO config: {yolo_config}")
        config_name = yolo_config
        evaluator_overrides = {
            "latency_topic": "/follower_1/measurement/inference_ms",
            "diagnostic_topic": "/follower_1/measurement/detection_box",
            "require_latency": True,
            "evidence_scope": (
                "YOLOv8n camera-only target measurement in Gazebo; not "
                "closed-loop control, physical-robot, or safety evidence"
            ),
        }
    else:
        raise ValueError(f"unsupported detector: {detector}")
    perception = Node(
        package="ee616_perception",
        executable=executable,
        namespace="follower_1",
        name="camera_measurement",
        parameters=[
            str(perception_share / "config" / config_name),
            {
                "horizontal_fov_rad": scenario["camera"]["horizontal_fov_rad"],
                "target_height_m": scenario["target"]["size"][2],
            },
        ],
        output="screen",
    )
    evaluator = Node(
        package="ee616_evaluation",
        executable="camera_gate_evaluator",
        name="camera_gate_evaluator",
        parameters=[
            {
                "scene": scene,
                "output_dir": output_dir,
                "horizontal_fov_rad": scenario["camera"]["horizontal_fov_rad"],
                "image_width": scenario["camera"]["width"],
                "image_height": scenario["camera"]["height"],
                "target_size": scenario["target"]["size"],
                "target_z": scenario["target"]["pose"][2],
                "target_yaw": scenario["target"]["pose"][5],
                "obstacles_xy_json": json.dumps(
                    [
                        [
                            obstacle["pose"][0],
                            obstacle["pose"][1],
                            obstacle["pose"][5],
                            obstacle["size"][0],
                            obstacle["size"][1],
                        ]
                        for obstacle in scenario["obstacles"]
                    ]
                ),
                **evaluator_overrides,
            }
        ],
        output="screen",
    )
    shutdown = RegisterEventHandler(
        OnProcessExit(
            target_action=evaluator,
            on_exit=[
                EmitEvent(
                    event=Shutdown(
                        reason="camera measurement evaluator completed"
                    )
                )
            ],
        )
    )
    return [simulation, perception, evaluator, shutdown]


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "detector",
                default_value="red_baseline",
                description="Perception backend: red_baseline or yolov8n.",
            ),
            DeclareLaunchArgument(
                "yolo_config",
                default_value="yolov8n_target.yaml",
                description="Installed YOLO parameter file.",
            ),
            DeclareLaunchArgument(
                "scene",
                default_value="camera_calibration",
                description="Scenario used for the measurement sweep.",
            ),
            DeclareLaunchArgument(
                "output_dir",
                default_value=(
                    "/workspace/work/ros2_ws/results/camera_measurement_gate"
                ),
                description="Directory for evaluation-only evidence.",
            ),
            OpaqueFunction(function=_configure),
        ]
    )
