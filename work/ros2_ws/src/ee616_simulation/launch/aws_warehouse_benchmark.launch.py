"""Launch the pinned AWS no-roof warehouse as an optional stress test."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from ament_index_python.packages import get_package_share_directory

from ee616_simulation.aws_world import prepare_aws_world
from launch import LaunchContext, LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, LogInfo, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _as_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError("gui must be true or false.")
    return normalized == "true"


def _generated_dir() -> Path:
    project_root = os.environ.get("EE616_PROJECT_ROOT")
    if project_root:
        return Path(project_root) / "work" / "ros2_ws" / "log" / "generated_scenarios"
    return Path(tempfile.gettempdir()) / "ee616_generated_scenarios"


def _configure(context: LaunchContext):
    package_share = Path(get_package_share_directory("ee616_simulation"))
    vendor_root = package_share / "vendor" / "aws_small_warehouse"
    source_world = (
        vendor_root
        / "worlds"
        / "no_roof_small_warehouse"
        / "no_roof_small_warehouse.world"
    )
    manifest = prepare_aws_world(source_world, _generated_dir())
    bridge_config = package_share / "config" / "camera_bridge.yaml"
    resource_path = str(vendor_root / "models")
    previous_resource_path = os.environ.get("GZ_SIM_RESOURCE_PATH")
    if previous_resource_path:
        resource_path = f"{resource_path}:{previous_resource_path}"

    command = ["gz", "sim", "-r", "-v", "3"]
    if not _as_bool(LaunchConfiguration("gui").perform(context)):
        command.append("-s")
    command.append(manifest["world_path"])
    return [
        LogInfo(msg=f"EE616_AWS_MANIFEST={manifest['manifest_path']}"),
        ExecuteProcess(
            cmd=command,
            output="screen",
            additional_env={"GZ_SIM_RESOURCE_PATH": resource_path},
        ),
        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            name="camera_bridge",
            parameters=[{"config_file": str(bridge_config)}],
            output="screen",
        ),
    ]


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "gui",
                default_value="false",
                description="Start the Gazebo graphical interface.",
            ),
            OpaqueFunction(function=_configure),
        ]
    )
