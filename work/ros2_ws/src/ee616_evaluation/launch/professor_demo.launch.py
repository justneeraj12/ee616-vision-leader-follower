"""Launch a GUI-only presentation run without touching frozen gate results."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchContext, LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


DEMO_MODES = {"pair_turn", "chain_straight", "chain_turn", "recovery"}


def _configure(context: LaunchContext):
    mode = LaunchConfiguration("mode").perform(context)
    output_root = Path(LaunchConfiguration("output_root").perform(context))
    if mode not in DEMO_MODES:
        raise ValueError(f"mode must be one of {sorted(DEMO_MODES)}")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = output_root / f"{timestamp}_{mode}"
    output_dir.mkdir(parents=True, exist_ok=True)
    evaluation_share = Path(get_package_share_directory("ee616_evaluation"))

    if mode == "pair_turn":
        launch_file = evaluation_share / "launch" / "pair_gate.launch.py"
        arguments = {
            "profile": "turn",
            "run_id": "run_01",
            "output_dir": str(output_dir),
            "gui": "true",
            "startup_extension_s": "8.0",
        }
        follower_count = 1
        disturbed_images = False
    elif mode in {"chain_straight", "chain_turn"}:
        launch_file = evaluation_share / "launch" / "chain_gate.launch.py"
        arguments = {
            "profile": "straight" if mode == "chain_straight" else "turn",
            "follower_count": "3",
            "run_id": "run_01",
            "output_dir": str(output_dir),
            "gui": "true",
            "startup_extension_s": "8.0",
        }
        follower_count = 3
        disturbed_images = False
    else:
        launch_file = evaluation_share / "launch" / "disturbance_gate.launch.py"
        arguments = {
            "scenario": "long_occlusion",
            "follower_count": "1",
            "run_id": "run_01",
            "output_dir": str(output_dir),
            "gui": "true",
            "startup_extension_s": "10.0",
        }
        follower_count = 1
        disturbed_images = True

    viewer = Node(
        package="ee616_evaluation",
        executable="demo_viewer",
        name="demo_viewer",
        parameters=[{
            "follower_count": follower_count,
            "camera_count": 1,
            "disturbed_images": disturbed_images,
            "use_sim_time": True,
        }],
        output="screen",
    )
    experiment = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(launch_file)),
        launch_arguments=arguments.items(),
    )
    return [
        LogInfo(msg=f"EE616_DEMO_OUTPUT={output_dir}"),
        viewer,
        experiment,
    ]


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        DeclareLaunchArgument("mode", default_value="pair_turn"),
        DeclareLaunchArgument(
            "output_root",
            default_value="/workspace/work/ros2_ws/results/professor_demos",
        ),
        OpaqueFunction(function=_configure),
    ])
