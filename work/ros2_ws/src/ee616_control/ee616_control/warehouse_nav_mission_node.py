"""Coordinate loading, Hybrid-A* planning, path tracking, and unloading."""

from __future__ import annotations

import json
import math

from action_msgs.msg import GoalStatus
from ee616_control.warehouse_mission import ROBOT_NAMES, cargo_position
from ee616_control.warehouse_nav_mission import (
    NAV_WAYPOINTS,
    build_loading_segments,
)
from geometry_msgs.msg import PoseStamped, Twist
from nav2_msgs.action import ComputePathToPose, FollowPath
from nav_msgs.msg import Path
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Float64, String


class WarehouseNavMissionNode(Node):
    """Use Nav2 only after the deterministic loading queue has completed."""

    def __init__(self) -> None:
        super().__init__("warehouse_nav_mission")
        self.declare_parameter("follower_count", 3)
        self.declare_parameter("startup_s", 10.0)
        self.declare_parameter("waypoint_dwell_s", 4.0)
        self.follower_count = int(self.get_parameter("follower_count").value)
        startup_s = float(self.get_parameter("startup_s").value)
        self.waypoint_dwell_s = float(
            self.get_parameter("waypoint_dwell_s").value
        )
        if not 0.5 <= self.waypoint_dwell_s <= 10.0:
            raise ValueError("waypoint_dwell_s must be between 0.5 and 10.0")
        self.robots = ROBOT_NAMES[: self.follower_count + 1]
        self.loading_segments = build_loading_segments(
            self.follower_count,
            startup_s=startup_s,
        )
        self.started_s = self._now_s()
        self.command_publisher = self.create_publisher(
            Twist, "/leader/cmd_vel", 10
        )
        self.state_publisher = self.create_publisher(
            String, "/warehouse_mission/state", 10
        )
        self.cargo_state_publisher = self.create_publisher(
            String, "/warehouse_mission/cargo_state", 10
        )
        self.planner_state_publisher = self.create_publisher(
            String, "/warehouse_nav/planner_state", 10
        )
        self.path_publisher = self.create_publisher(
            Path, "/warehouse_nav/planned_path", 10
        )
        self.cargo_publishers = {
            robot: self.create_publisher(
                Float64, f"/warehouse_mission/{robot}/cargo_position", 10
            )
            for robot in self.robots
        }
        self.planner_client = ActionClient(
            self, ComputePathToPose, "/compute_path_to_pose"
        )
        self.controller_client = ActionClient(
            self, FollowPath, "/follow_path"
        )
        self.navigation_started = False
        self.action_active = False
        self.waypoint_index = 0
        self.state = "SETTLE"
        self.failure = ""
        self.navigation_complete_s: float | None = None
        self.next_goal_after_s = 0.0
        self.planning_records: list[dict] = []
        self.scan_snapshot: dict | None = None
        self.create_subscription(LaserScan, "/leader/scan", self._scan, 10)
        self.timer = self.create_timer(0.05, self._tick)

    def _scan(self, message: LaserScan) -> None:
        samples = [
            (message.angle_min + index * message.angle_increment, distance)
            for index, distance in enumerate(message.ranges)
            if math.isfinite(distance)
            and message.range_min <= distance <= message.range_max
        ]
        if not samples:
            self.scan_snapshot = {"valid_samples": 0}
            return

        def sector_min(center: float) -> float | None:
            values = [
                distance
                for angle, distance in samples
                if abs(math.atan2(
                    math.sin(angle - center), math.cos(angle - center)
                )) <= 0.35
            ]
            return min(values) if values else None

        nearest_angle, nearest_range = min(samples, key=lambda item: item[1])
        self.scan_snapshot = {
            "valid_samples": len(samples),
            "nearest_range_m": nearest_range,
            "nearest_angle_deg": math.degrees(nearest_angle),
            "front_min_m": sector_min(0.0),
            "left_min_m": sector_min(math.pi / 2.0),
            "rear_min_m": sector_min(math.pi),
            "right_min_m": sector_min(-math.pi / 2.0),
        }

    def _now_s(self) -> float:
        return self.get_clock().now().nanoseconds * 1.0e-9

    def _loading_output(self, elapsed_s: float):
        cargo = {name: False for name in self.robots}
        remaining = max(0.0, elapsed_s)
        for segment in self.loading_segments:
            if segment.cargo_action is not None:
                robot, loaded = segment.cargo_action
                cargo[robot] = loaded
            if remaining < segment.duration_s:
                return segment.state, segment.linear_mps, cargo, False
            remaining -= segment.duration_s
        return "WAIT_NAV2", 0.0, cargo, True

    def _dropoff_output(self, now_s: float):
        cargo = {name: True for name in self.robots}
        elapsed_s = now_s - self.navigation_complete_s
        if elapsed_s < 2.5:
            return "DROPOFF_SETTLE", cargo
        elapsed_s -= 2.5
        for robot in self.robots:
            cargo[robot] = False
            if elapsed_s < 1.5:
                return f"UNLOAD_{robot.upper()}", cargo
            elapsed_s -= 1.5
        return "COMPLETE", cargo

    def _publish_state(self, state: str, cargo: dict[str, bool]) -> None:
        self.state = state
        message = String()
        message.data = state
        self.state_publisher.publish(message)
        cargo_message = String()
        cargo_message.data = json.dumps(cargo, sort_keys=True)
        self.cargo_state_publisher.publish(cargo_message)
        for robot, loaded in cargo.items():
            position = Float64()
            position.data = cargo_position(loaded)
            self.cargo_publishers[robot].publish(position)

    def _publish_planner_state(self) -> None:
        message = String()
        message.data = json.dumps({
            "algorithm": "Nav2 SmacPlannerHybrid (Hybrid-A*)",
            "controller": "Nav2 RegulatedPurePursuitController",
            "localization": "Nav2 AMCL",
            "waypoint_index": self.waypoint_index,
            "waypoint_count": len(NAV_WAYPOINTS),
            "action_active": self.action_active,
            "failure": self.failure or None,
            "plans": self.planning_records,
            "scan_snapshot": self.scan_snapshot,
        }, sort_keys=True)
        self.planner_state_publisher.publish(message)

    def _tick(self) -> None:
        now_s = self._now_s()
        elapsed_s = now_s - self.started_s
        if not self.navigation_started:
            state, linear_mps, cargo, loading_complete = self._loading_output(
                elapsed_s
            )
            command = Twist()
            command.linear.x = linear_mps
            self.command_publisher.publish(command)
            self._publish_state(state, cargo)
            if loading_complete:
                self.navigation_started = True
                self.next_goal_after_s = now_s + 0.5
            return

        cargo = {name: True for name in self.robots}
        if self.failure:
            self._publish_state("NAV_FAILED", cargo)
        elif self.navigation_complete_s is not None:
            state, cargo = self._dropoff_output(now_s)
            self._publish_state(state, cargo)
        else:
            self._publish_state(self.state, cargo)
            if not self.action_active and now_s >= self.next_goal_after_s:
                self._request_plan()
        self._publish_planner_state()

    def _request_plan(self) -> None:
        if self.waypoint_index >= len(NAV_WAYPOINTS):
            self.navigation_complete_s = self._now_s()
            self.command_publisher.publish(Twist())
            return
        if not self.planner_client.server_is_ready():
            self.state = "WAIT_NAV2_PLANNER"
            self.next_goal_after_s = self._now_s() + 0.5
            return
        waypoint = NAV_WAYPOINTS[self.waypoint_index]
        self.state = f"PLAN_{waypoint.name}"
        self.action_active = True
        goal = ComputePathToPose.Goal()
        goal.goal = PoseStamped()
        goal.goal.header.frame_id = "map"
        goal.goal.header.stamp = self.get_clock().now().to_msg()
        goal.goal.pose.position.x = waypoint.x_m
        goal.goal.pose.position.y = waypoint.y_m
        goal.goal.pose.orientation.z = math.sin(waypoint.yaw_rad / 2.0)
        goal.goal.pose.orientation.w = math.cos(waypoint.yaw_rad / 2.0)
        goal.planner_id = "GridBased"
        goal.use_start = False
        future = self.planner_client.send_goal_async(goal)
        future.add_done_callback(self._plan_goal_response)

    def _plan_goal_response(self, future) -> None:
        goal_handle = future.result()
        if not goal_handle.accepted:
            self._fail("Hybrid-A* planner rejected the goal")
            return
        goal_handle.get_result_async().add_done_callback(self._plan_result)

    def _plan_result(self, future) -> None:
        response = future.result()
        result = response.result
        if response.status != GoalStatus.STATUS_SUCCEEDED or result.error_code:
            self._fail(
                f"Hybrid-A* planning failed: {result.error_code} {result.error_msg}"
            )
            return
        if len(result.path.poses) < 2:
            self._fail("Hybrid-A* returned an empty path")
            return
        length_m = sum(
            math.hypot(
                current.pose.position.x - previous.pose.position.x,
                current.pose.position.y - previous.pose.position.y,
            )
            for previous, current in zip(
                result.path.poses,
                result.path.poses[1:],
            )
        )
        planning_s = (
            result.planning_time.sec
            + result.planning_time.nanosec * 1.0e-9
        )
        waypoint = NAV_WAYPOINTS[self.waypoint_index]
        self.planning_records.append({
            "waypoint": waypoint.name,
            "path_length_m": length_m,
            "planning_time_s": planning_s,
            "path_pose_count": len(result.path.poses),
            "path_start_xy_m": [
                result.path.poses[0].pose.position.x,
                result.path.poses[0].pose.position.y,
            ],
            "path_end_xy_m": [
                result.path.poses[-1].pose.position.x,
                result.path.poses[-1].pose.position.y,
            ],
            "path_y_bounds_m": [
                min(pose.pose.position.y for pose in result.path.poses),
                max(pose.pose.position.y for pose in result.path.poses),
            ],
        })
        self.path_publisher.publish(result.path)
        self._request_follow(result.path)

    def _request_follow(self, path: Path) -> None:
        if not self.controller_client.server_is_ready():
            self._fail("regulated path controller action server is unavailable")
            return
        waypoint = NAV_WAYPOINTS[self.waypoint_index]
        self.state = f"NAV_{waypoint.name}"
        goal = FollowPath.Goal()
        goal.path = path
        goal.controller_id = "FollowPath"
        goal.goal_checker_id = "general_goal_checker"
        goal.progress_checker_id = "progress_checker"
        future = self.controller_client.send_goal_async(goal)
        future.add_done_callback(self._follow_goal_response)

    def _follow_goal_response(self, future) -> None:
        goal_handle = future.result()
        if not goal_handle.accepted:
            self._fail("regulated path controller rejected the path")
            return
        goal_handle.get_result_async().add_done_callback(self._follow_result)

    def _follow_result(self, future) -> None:
        response = future.result()
        result = response.result
        if response.status != GoalStatus.STATUS_SUCCEEDED or result.error_code:
            self._fail(
                "regulated path tracking failed: "
                f"{result.error_code} {result.error_msg}"
            )
            return
        self.waypoint_index += 1
        self.action_active = False
        self.next_goal_after_s = self._now_s() + self.waypoint_dwell_s
        if self.waypoint_index >= len(NAV_WAYPOINTS):
            self.navigation_complete_s = self._now_s()

    def _fail(self, reason: str) -> None:
        self.failure = reason
        self.action_active = False
        self.command_publisher.publish(Twist())
        self.get_logger().error(reason)

    def destroy_node(self):
        if rclpy.ok():
            self.command_publisher.publish(Twist())
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = WarehouseNavMissionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
