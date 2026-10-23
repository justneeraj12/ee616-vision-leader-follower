"""Launch the pair-first or full mapped Hybrid-A* warehouse mission."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from ee616_simulation.warehouse_nav_world import (
    WORLD_NAME_PREFIX,
    render_warehouse_nav_map,
    render_warehouse_nav_world,
)
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
        return (
            Path(project_root)
            / "work"
            / "ros2_ws"
            / "log"
            / "generated_nav_worlds"
        )
    return Path(tempfile.gettempdir()) / "ee616_generated_nav_worlds"


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

    simulation_share = Path(get_package_share_directory("ee616_simulation"))
    perception_share = Path(get_package_share_directory("ee616_perception"))
    control_share = Path(get_package_share_directory("ee616_control"))
    generated_dir = _generated_dir()
    world_path = render_warehouse_nav_world(follower_count, generated_dir)
    map_path = render_warehouse_nav_map(generated_dir)
    nav_params = control_share / "config" / "warehouse_nav2.yaml"
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
            package="ros_gz_bridge",
            executable="parameter_bridge",
            name="warehouse_nav_bridge",
            parameters=[{
                "config_file": str(
                    simulation_share / "config" / "warehouse_nav_bridge.yaml"
                )
            }],
            output="screen",
        ),
        Node(
            package="ee616_control",
            executable="leader_map_tf",
            parameters=[{"use_sim_time": True}],
            output="screen",
        ),
        Node(
            package="nav2_map_server",
            executable="map_server",
            name="map_server",
            parameters=[str(nav_params), {
                "yaml_filename": str(map_path),
                "use_sim_time": True,
            }],
            output="screen",
        ),
        Node(
            package="nav2_amcl",
            executable="amcl",
            name="amcl",
            parameters=[str(nav_params)],
            output="screen",
        ),
        Node(
            package="nav2_planner",
            executable="planner_server",
            name="planner_server",
            parameters=[str(nav_params)],
            output="screen",
        ),
        Node(
            package="nav2_controller",
            executable="controller_server",
            name="controller_server",
            parameters=[str(nav_params)],
            remappings=[("cmd_vel", "/leader/cmd_vel")],
            output="screen",
        ),
        Node(
            package="nav2_lifecycle_manager",
            executable="lifecycle_manager",
            name="lifecycle_manager_navigation",
            parameters=[str(nav_params)],
            output="screen",
        ),
        Node(
            package="ee616_control",
            executable="warehouse_nav_mission",
            parameters=[{
                "follower_count": follower_count,
                "startup_s": startup_s,
                "waypoint_dwell_s": 4.0,
                "use_sim_time": True,
            }],
            output="screen",
        ),
    ]
    if gui:
        track_message = (
            "track_mode: 4, "
            'follow_target: {name: "follower_1", type: 2}, '
            'track_target: {name: "follower_1", type: 2}, '
            "follow_offset: {x: -4.0, y: -4.0, z: 3.5}, "
            "follow_pgain: 0.10, track_pgain: 0.12"
        )
        track_command = (
            "for attempt in $(seq 1 60); do "
            "if gz topic -i -t /gui/track 2>/dev/null | "
            "grep -q '^Subscribers'; then "
            "gz topic -t /gui/track -m gz.msgs.CameraTrack "
            f"-p '{track_message}'; exit $?; "
            "fi; sleep 1; done; "
            "echo 'Timed out waiting for the Gazebo camera tracker' >&2; exit 1"
        )
        actions.insert(1, TimerAction(
            period=2.0,
            actions=[ExecuteProcess(
                cmd=[
                    "gz", "sim", "-g", "-v", "3",
                    "--render-engine-gui", render_engine,
                ],
                additional_env={"GZ_SIM_RESOURCE_PATH": resource_path},
                output="screen",
            )],
        ))
        actions.insert(2, TimerAction(
            # The process waits for the CameraTracking subscriber instead of
            # sending a one-shot message while the GUI is still loading.
            period=5.0,
            actions=[ExecuteProcess(
                cmd=["bash", "-lc", track_command],
                output="screen",
            )],
        ))

    for index in range(1, follower_count + 1):
        namespace = f"follower_{index}"
        actions.extend([
            Node(
                package="ee616_perception",
                executable="yolo_measurement",
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
                package="ee616_control",
                executable="follower_controller",
                namespace=namespace,
                parameters=[
                    str(control_share / "config" / "pair_control.yaml"),
                    {
                        "innovation_gate_sq": 25.0,
                        "max_measurement_range_m": 2.5,
                        "bearing_slowdown_rad": 0.52,
                        "use_sim_time": True,
                    },
                ],
                output="screen",
            ),
        ])

    evaluator = Node(
        package="ee616_evaluation",
        executable="warehouse_mission_evaluator",
        name="warehouse_nav_mission_evaluator",
        parameters=[{
            "follower_count": follower_count,
            "run_id": run_id,
            "output_dir": output_dir,
            "duration_s": 260.0,
            "world_name": f"{WORLD_NAME_PREFIX}_{follower_count}",
            "loading_x_m": -10.0,
            "loading_y_m": -6.0,
            "dropoff_x_m": -10.0,
            "dropoff_y_m": -1.0,
            "require_nav2": True,
            "expected_nav_waypoints": 4,
            "use_sim_time": True,
        }],
        output="screen",
    )
    actions.extend([
        evaluator,
        RegisterEventHandler(OnProcessExit(
            target_action=evaluator,
            on_exit=[EmitEvent(event=Shutdown(reason="warehouse Nav2 evaluator completed"))],
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
            default_value="/workspace/work/ros2_ws/results/warehouse_nav_mission",
        ),
        OpaqueFunction(function=_configure),
    ])
