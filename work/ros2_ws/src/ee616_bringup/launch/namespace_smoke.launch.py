from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package="ee616_bringup",
                executable="namespace_probe",
                namespace="leader",
                parameters=[{"expected_id": "leader"}],
                output="screen",
            ),
            Node(
                package="ee616_bringup",
                executable="namespace_probe",
                namespace="follower_1",
                parameters=[{"expected_id": "follower_1"}],
                output="screen",
            ),
        ]
    )
