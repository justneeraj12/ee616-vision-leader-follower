"""Launch the accepted combined disturbance scenario with timing observation."""

from __future__ import annotations

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    evaluation_share = Path(get_package_share_directory("ee616_evaluation"))
    run_id = LaunchConfiguration("run_id")
    output_dir = LaunchConfiguration("output_dir")
    accepted_scenario = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(evaluation_share / "launch" / "disturbance_gate.launch.py")
        ),
        launch_arguments={
            "scenario": "combined",
            "follower_count": "3",
            "run_id": run_id,
            "output_dir": output_dir,
        }.items(),
    )
    timing_evaluator = Node(
        package="ee616_evaluation",
        executable="timing_gate_evaluator",
        name="timing_gate_evaluator",
        parameters=[{
            "follower_count": 3,
            "run_id": run_id,
            "output_dir": output_dir,
            "duration_s": 49.0,
            "warmup_s": 8.0,
            "use_sim_time": True,
        }],
        output="screen",
    )
    return LaunchDescription([
        DeclareLaunchArgument("run_id", default_value="run_01"),
        DeclareLaunchArgument(
            "output_dir",
            default_value="/workspace/work/ros2_ws/results/timing_gate",
        ),
        accepted_scenario,
        timing_evaluator,
    ])
