from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    package_share = Path(get_package_share_directory("ee616_simulation"))
    world = package_share / "worlds" / "camera_smoke.sdf"
    bridge_config = package_share / "config" / "camera_bridge.yaml"

    return LaunchDescription(
        [
            ExecuteProcess(
                cmd=["gz", "sim", "-r", "-s", str(world)],
                output="screen",
            ),
            Node(
                package="ros_gz_bridge",
                executable="parameter_bridge",
                name="camera_bridge",
                parameters=[{"config_file": str(bridge_config)}],
                output="screen",
            ),
        ]
    )
