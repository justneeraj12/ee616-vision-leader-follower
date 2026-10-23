"""Evaluation-only recorder for the staged warehouse cargo mission."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys
import time

from ee616_control.warehouse_mission import ROBOT_NAMES
from ee616_evaluation.pair_gate_evaluator import percentile
from ee616_evaluation.pose_text import parse_entity_pose, read_gz_topic_text
from geometry_msgs.msg import Twist, Vector3Stamped
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String


CSV_FIELDS = [
    "elapsed_s", "mission_state", "follower_count", "follower_index",
    "predecessor", "control_state", "true_range_m", "true_bearing_deg",
    "spacing_error_m", "estimated_range_m", "estimated_bearing_deg",
    "measurement_age_s", "linear_cmd_mps", "angular_cmd_rps",
    "center_distance_m", "collision_sample", "inference_ms",
    "leader_x_m", "leader_y_m",
]
TRANSPORT_STATES = {"WAREHOUSE_AISLE", "WAREHOUSE_TURN", "APPROACH_DROPOFF"}
WAREHOUSE_SHELF_X_M = (-3.0, 0.0, 3.0)
WAREHOUSE_SHELF_Y_M = (-3.5, 2.0, 7.5)
WAREHOUSE_SHELF_HALF_X_M = 1.98
WAREHOUSE_SHELF_HALF_Y_M = 0.48
WAREHOUSE_WALL_INNER_X_M = 18.70
WAREHOUSE_WALL_INNER_Y_M = 11.70
EVALUATION_ROBOT_RADIUS_M = 0.36


def warehouse_obstacle_collision(
    x_m: float,
    y_m: float,
    robot_radius_m: float = EVALUATION_ROBOT_RADIUS_M,
) -> bool:
    """Return whether a circular robot footprint intersects mapped static geometry."""
    if (
        abs(x_m) + robot_radius_m >= WAREHOUSE_WALL_INNER_X_M
        or abs(y_m) + robot_radius_m >= WAREHOUSE_WALL_INNER_Y_M
    ):
        return True
    for shelf_x_m in WAREHOUSE_SHELF_X_M:
        for shelf_y_m in WAREHOUSE_SHELF_Y_M:
            dx_m = max(abs(x_m - shelf_x_m) - WAREHOUSE_SHELF_HALF_X_M, 0.0)
            dy_m = max(abs(y_m - shelf_y_m) - WAREHOUSE_SHELF_HALF_Y_M, 0.0)
            if math.hypot(dx_m, dy_m) <= robot_radius_m:
                return True
    return False


class WarehouseMissionEvaluator(Node):
    """Measure the mission without feeding Gazebo truth into the robot stack."""

    def __init__(self) -> None:
        super().__init__("warehouse_mission_evaluator")
        self.declare_parameter("follower_count", 3)
        self.declare_parameter("run_id", "run_01")
        self.declare_parameter("output_dir", "results/warehouse_mission")
        self.declare_parameter("duration_s", 100.0)
        self.declare_parameter("desired_range_m", 1.5)
        self.declare_parameter("world_name", "")
        self.declare_parameter("loading_x_m", -5.0)
        self.declare_parameter("loading_y_m", 0.0)
        self.declare_parameter("dropoff_x_m", 12.3)
        self.declare_parameter("dropoff_y_m", 3.9)
        self.declare_parameter("require_nav2", False)
        self.declare_parameter("expected_nav_waypoints", 5)
        self.follower_count = int(self.get_parameter("follower_count").value)
        if self.follower_count not in {1, 3}:
            raise ValueError("follower_count must be 1 or 3")
        self.run_id = str(self.get_parameter("run_id").value)
        self.output_dir = Path(str(self.get_parameter("output_dir").value))
        self.duration_s = float(self.get_parameter("duration_s").value)
        self.desired_range_m = float(self.get_parameter("desired_range_m").value)
        configured_world = str(self.get_parameter("world_name").value)
        self.world_name = configured_world or f"warehouse_mission_{self.follower_count}"
        self.loading_station = (
            float(self.get_parameter("loading_x_m").value),
            float(self.get_parameter("loading_y_m").value),
        )
        self.dropoff_station = (
            float(self.get_parameter("dropoff_x_m").value),
            float(self.get_parameter("dropoff_y_m").value),
        )
        self.require_nav2 = bool(self.get_parameter("require_nav2").value)
        self.expected_nav_waypoints = int(
            self.get_parameter("expected_nav_waypoints").value
        )
        indexes = range(1, self.follower_count + 1)
        self.rows: list[dict] = []
        self.control_states = {index: "UNSEEN" for index in indexes}
        self.estimates = {index: [math.nan, math.nan, math.inf] for index in indexes}
        self.commands = {index: [0.0, 0.0] for index in indexes}
        self.inference_ms = {index: None for index in indexes}
        self.last_estimate_stamp_s = {index: None for index in indexes}
        self.control_periods_ms = {index: [] for index in indexes}
        self.mission_state = "UNSEEN"
        self.cargo_state: dict[str, bool] = {}
        self.state_sequence: list[str] = []
        self.planner_state: dict = {}
        self.complete_seen_s: float | None = None
        self.nav_failure_seen_s: float | None = None
        self.dropoff_errors: list[float] = []
        self.station_errors: dict[str, list[float]] = {
            name: [] for name in ROBOT_NAMES[: self.follower_count + 1]
        }
        self.warehouse_obstacle_collision_samples = {
            name: 0 for name in ROBOT_NAMES[: self.follower_count + 1]
        }
        self.started_sim_s: float | None = None
        self.started_wall_s = time.monotonic()
        self.last_elapsed_s = 0.0
        self.failure = ""
        self.exit_code = 1
        self.done = False
        self.create_subscription(String, "/warehouse_mission/state", self._state, 10)
        self.create_subscription(
            String, "/warehouse_nav/planner_state", self._planner_state, 10
        )
        self.create_subscription(
            String, "/warehouse_mission/cargo_state", self._cargo, 10
        )
        for index in indexes:
            prefix = f"/follower_{index}"
            self.create_subscription(
                String, f"{prefix}/control/state",
                lambda message, i=index: self._control_state(i, message), 10,
            )
            self.create_subscription(
                Vector3Stamped, f"{prefix}/control/estimate",
                lambda message, i=index: self._estimate(i, message), 10,
            )
            self.create_subscription(
                Twist, f"{prefix}/cmd_vel",
                lambda message, i=index: self._command(i, message), 10,
            )
            self.create_subscription(
                Float32, f"{prefix}/measurement/inference_ms",
                lambda message, i=index: self._latency(i, message), 10,
            )
        self.timer = self.create_timer(0.2, self._sample)

    @property
    def pose_topic(self) -> str:
        return f"/world/{self.world_name}/pose/info"

    def _state(self, message: String) -> None:
        self.mission_state = message.data
        if not self.state_sequence or self.state_sequence[-1] != message.data:
            self.state_sequence.append(message.data)
        if message.data == "COMPLETE" and self.complete_seen_s is None:
            self.complete_seen_s = self.get_clock().now().nanoseconds * 1.0e-9
        if message.data == "NAV_FAILED" and self.nav_failure_seen_s is None:
            self.nav_failure_seen_s = self.get_clock().now().nanoseconds * 1.0e-9

    def _planner_state(self, message: String) -> None:
        try:
            parsed = json.loads(message.data)
            if isinstance(parsed, dict):
                self.planner_state = parsed
        except (json.JSONDecodeError, TypeError):
            self.get_logger().warning("ignored malformed planner state")

    def _cargo(self, message: String) -> None:
        try:
            parsed = json.loads(message.data)
            self.cargo_state = {str(key): bool(value) for key, value in parsed.items()}
        except (json.JSONDecodeError, TypeError):
            self.get_logger().warning("ignored malformed cargo state")

    def _control_state(self, index: int, message: String) -> None:
        self.control_states[index] = message.data

    def _estimate(self, index: int, message: Vector3Stamped) -> None:
        stamp_s = message.header.stamp.sec + message.header.stamp.nanosec * 1.0e-9
        previous = self.last_estimate_stamp_s[index]
        if previous is not None and stamp_s > previous:
            self.control_periods_ms[index].append((stamp_s - previous) * 1000.0)
        self.last_estimate_stamp_s[index] = stamp_s
        self.estimates[index] = [message.vector.x, message.vector.y, message.vector.z]

    def _command(self, index: int, message: Twist) -> None:
        self.commands[index] = [message.linear.x, message.angular.z]

    def _latency(self, index: int, message: Float32) -> None:
        value = float(message.data)
        self.inference_ms[index] = value if math.isfinite(value) else None

    def _read_poses(self) -> dict:
        message = read_gz_topic_text(self.pose_topic)
        names = ROBOT_NAMES[: self.follower_count + 1]
        return {name: parse_entity_pose(message, name) for name in names}

    def _sample(self) -> None:
        if self.done:
            return
        now_sim_s = self.get_clock().now().nanoseconds * 1.0e-9
        if self.started_sim_s is None:
            self.started_sim_s = now_sim_s
        elapsed_s = max(0.0, now_sim_s - self.started_sim_s)
        self.last_elapsed_s = elapsed_s
        if self.complete_seen_s is not None and now_sim_s - self.complete_seen_s >= 1.0:
            self._finish("")
            return
        if (
            self.nav_failure_seen_s is not None
            and now_sim_s - self.nav_failure_seen_s >= 1.0
        ):
            planner_failure = self.planner_state.get("failure", "unknown Nav2 failure")
            self._finish(f"warehouse navigation failed: {planner_failure}")
            return
        if elapsed_s >= self.duration_s:
            self._finish("")
            return
        try:
            poses = self._read_poses()
        except (RuntimeError, ValueError, subprocess.SubprocessError) as exc:
            if time.monotonic() - self.started_wall_s > 8.0:
                self._finish(f"unable to read warehouse ground truth: {exc}")
            return

        for robot, pose in poses.items():
            if warehouse_obstacle_collision(pose.x, pose.y):
                self.warehouse_obstacle_collision_samples[robot] += 1

        if self.mission_state.startswith("LOAD_"):
            robot = self.mission_state.removeprefix("LOAD_").lower()
            if robot in poses:
                pose = poses[robot]
                self.station_errors[robot].append(math.hypot(
                    pose.x - self.loading_station[0],
                    pose.y - self.loading_station[1],
                ))

        if self.mission_state == "DROPOFF_SETTLE":
            pose = poses["leader"]
            self.dropoff_errors.append(math.hypot(
                pose.x - self.dropoff_station[0],
                pose.y - self.dropoff_station[1],
            ))

        for index in range(1, self.follower_count + 1):
            follower = poses[f"follower_{index}"]
            predecessor_name = "leader" if index == 1 else f"follower_{index - 1}"
            predecessor = poses[predecessor_name]
            camera_x = follower.x + math.cos(follower.yaw) * 0.28
            camera_y = follower.y + math.sin(follower.yaw) * 0.28
            target_x = predecessor.x - math.cos(predecessor.yaw) * 0.30
            target_y = predecessor.y - math.sin(predecessor.yaw) * 0.30
            dx = target_x - camera_x
            dy = target_y - camera_y
            forward = math.cos(follower.yaw) * dx + math.sin(follower.yaw) * dy
            left = -math.sin(follower.yaw) * dx + math.cos(follower.yaw) * dy
            true_range = math.hypot(forward, left)
            center_distance = math.hypot(
                predecessor.x - follower.x, predecessor.y - follower.y
            )
            estimate = self.estimates[index]
            command = self.commands[index]
            self.rows.append({
                "elapsed_s": elapsed_s,
                "mission_state": self.mission_state,
                "follower_count": self.follower_count,
                "follower_index": index,
                "predecessor": predecessor_name,
                "control_state": self.control_states[index],
                "true_range_m": true_range,
                "true_bearing_deg": math.degrees(math.atan2(left, forward)),
                "spacing_error_m": true_range - self.desired_range_m,
                "estimated_range_m": estimate[0],
                "estimated_bearing_deg": math.degrees(estimate[1]),
                "measurement_age_s": estimate[2],
                "linear_cmd_mps": command[0],
                "angular_cmd_rps": command[1],
                "center_distance_m": center_distance,
                "collision_sample": int(center_distance < 0.65),
                "inference_ms": self.inference_ms[index],
                "leader_x_m": poses["leader"].x,
                "leader_y_m": poses["leader"].y,
            })

    def _finish(self, failure: str) -> None:
        if self.done:
            return
        self.done = True
        self.failure = failure
        self._write_results()
        self.exit_code = 0 if not failure else 1
        if failure:
            self.get_logger().error(failure)
        rclpy.shutdown()

    def _write_results(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        stem = f"warehouse_mission_{self.follower_count}_{self.run_id}"
        with (self.output_dir / f"{stem}_samples.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(self.rows)

        followers = {}
        all_checks: list[bool] = []
        for index in range(1, self.follower_count + 1):
            evaluated = [
                row for row in self.rows
                if row["follower_index"] == index
                and (
                    row["mission_state"] in TRANSPORT_STATES
                    or row["mission_state"].startswith("NAV_")
                )
            ]
            errors = [row["spacing_error_m"] for row in evaluated]
            rmse = (
                math.sqrt(statistics.fmean(error * error for error in errors))
                if errors else None
            )
            track_fraction = (
                sum(row["control_state"] == "TRACK" for row in evaluated)
                / len(evaluated) if evaluated else 0.0
            )
            bounded = all(
                0.0 <= row["linear_cmd_mps"] <= 0.600001
                and abs(row["angular_cmd_rps"]) <= 0.800001
                for row in evaluated
            )
            period_p95 = percentile(self.control_periods_ms[index], 0.95)
            latency_p95 = percentile(
                [row["inference_ms"] for row in evaluated if row["inference_ms"] is not None],
                0.95,
            )
            checks = {
                "transport_spacing_rmse": rmse is not None
                and rmse <= (0.20 if index == 1 else 0.25),
                "collision_samples": sum(row["collision_sample"] for row in evaluated) == 0,
                "bounded_commands": bounded,
                "control_period_p95": period_p95 is not None and period_p95 <= 66.7,
                "track_fraction": track_fraction >= 0.90,
                "inference_latency_p95": latency_p95 is not None and latency_p95 <= 66.7,
            }
            all_checks.extend(checks.values())
            followers[str(index)] = {
                "predecessor": "leader" if index == 1 else f"follower_{index - 1}",
                "transport_spacing_rmse_m": rmse,
                "minimum_center_distance_m": min(
                    (row["center_distance_m"] for row in evaluated), default=None
                ),
                "collision_samples": sum(row["collision_sample"] for row in evaluated),
                "track_fraction": track_fraction,
                "control_period_p95_ms": period_p95,
                "inference_latency_p95_ms": latency_p95,
                "bounded_commands": bounded,
                "checks": checks,
            }

        robots = ROBOT_NAMES[: self.follower_count + 1]
        expected_loads = [f"LOAD_{name.upper()}" for name in robots]
        expected_unloads = [f"UNLOAD_{name.upper()}" for name in robots]
        observed_loads = [state for state in self.state_sequence if state.startswith("LOAD_")]
        observed_unloads = [
            state for state in self.state_sequence if state.startswith("UNLOAD_")
        ]
        station_max = {
            robot: max(errors) if errors else None
            for robot, errors in self.station_errors.items()
        }
        wall_elapsed_s = max(time.monotonic() - self.started_wall_s, 1.0e-6)
        real_time_factor = self.last_elapsed_s / wall_elapsed_s
        mission_checks = {
            "route_complete": "COMPLETE" in self.state_sequence,
            "load_order": observed_loads == expected_loads,
            "unload_order": observed_unloads == expected_unloads,
            "loading_station_accuracy": all(
                error is not None and error <= 0.40 for error in station_max.values()
            ),
            "cargo_empty_at_completion": bool(self.cargo_state)
            and not any(self.cargo_state.values()),
            "real_time_factor": real_time_factor >= 0.90,
            "warehouse_obstacle_collisions": not any(
                self.warehouse_obstacle_collision_samples.values()
            ),
        }
        if self.require_nav2:
            plans = self.planner_state.get("plans", [])
            scan_snapshot = self.planner_state.get("scan_snapshot") or {}
            mission_checks.update({
                "hybrid_astar_plans": (
                    self.planner_state.get("algorithm")
                    == "Nav2 SmacPlannerHybrid (Hybrid-A*)"
                    and len(plans) == self.expected_nav_waypoints
                    and all(record.get("path_length_m", 0.0) > 0.0 for record in plans)
                ),
                "regulated_path_controller": (
                    self.planner_state.get("controller")
                    == "Nav2 RegulatedPurePursuitController"
                ),
                "amcl_localization": (
                    self.planner_state.get("localization") == "Nav2 AMCL"
                ),
                "leader_lidar_received": scan_snapshot.get("valid_samples", 0) > 0,
                "dropoff_station_accuracy": bool(self.dropoff_errors)
                and self.dropoff_errors[-1] <= 0.50,
                "planner_reported_no_failure": not self.planner_state.get("failure"),
            })
        all_checks.extend(mission_checks.values())
        summary = {
            "follower_count": self.follower_count,
            "run_id": self.run_id,
            "sample_count": len(self.rows),
            "mission_state_sequence": self.state_sequence,
            "observed_load_sequence": observed_loads,
            "observed_unload_sequence": observed_unloads,
            "loading_station_max_error_m": station_max,
            "followers": followers,
            "real_time_factor": real_time_factor,
            "wall_elapsed_s": wall_elapsed_s,
            "sim_elapsed_s": self.last_elapsed_s,
            "mission_checks": mission_checks,
            "warehouse_obstacle_collision_samples": (
                self.warehouse_obstacle_collision_samples
            ),
            "planner_state": self.planner_state or None,
            "dropoff_station_max_error_m": (
                max(self.dropoff_errors) if self.dropoff_errors else None
            ),
            "dropoff_station_final_error_m": (
                self.dropoff_errors[-1] if self.dropoff_errors else None
            ),
            "failure": self.failure or None,
            "status": "pass" if not self.failure and all(all_checks) else "fail",
            "ground_truth_boundary": (
                f"Gazebo {self.pose_topic} was read only by ee616_evaluation and was not "
                "published to perception, estimation, supervision, or control."
            ),
            "scope": (
                "Simulated warehouse formation-transport mission with scripted visual cargo; "
                "not manipulation, physical-robot, throughput, or production-safety evidence."
            ),
        }
        (self.output_dir / f"{stem}_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = WarehouseMissionEvaluator()
    try:
        rclpy.spin(node)
    finally:
        exit_code = node.exit_code
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    if exit_code:
        print("Warehouse mission evaluator failed; see summary.", file=sys.stderr)
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
