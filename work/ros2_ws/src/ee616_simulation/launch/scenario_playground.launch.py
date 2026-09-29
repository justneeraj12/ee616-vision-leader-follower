"""Launch one deterministic EE 616 warehouse scenario."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from ament_index_python.packages import get_package_share_directory

from ee616_simulation.scenario_builder import SCENARIO_NAME, render_scenario
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
    scenario_name = LaunchConfiguration("scenario").perform(context)
    if not SCENARIO_NAME.fullmatch(scenario_name):
        raise ValueError("scenario contains unsupported characters.")
    source = package_share / "scenarios" / f"{scenario_name}.yaml"
    if not source.is_file() or scenario_name == "base":
        choices = sorted(
            path.stem
            for path in (package_share / "scenarios").glob("*.yaml")
            if path.stem != "base"
        )
        raise ValueError(
            f"Unknown scenario {scenario_name!r}. Available: {', '.join(choices)}"
        )
    manifest = render_scenario(source, _generated_dir())
    bridge_config = package_share / "config" / "camera_bridge.yaml"

    command = ["gz", "sim", "-r", "-v", "3"]
    if not _as_bool(LaunchConfiguration("gui").perform(context)):
        command.append("-s")
    command.append(manifest["world_path"])
    return [
        LogInfo(msg=f"EE616_SCENARIO_MANIFEST={manifest['manifest_path']}"),
        ExecuteProcess(cmd=command, output="screen"),
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
                "scenario",
                default_value="straight_aisle",
                description="Installed scenario name without the .yaml suffix.",
            ),
            DeclareLaunchArgument(
                "gui",
                default_value="true",
                description="Start the Gazebo graphical interface.",
            ),
            OpaqueFunction(function=_configure),
        ]
    )
