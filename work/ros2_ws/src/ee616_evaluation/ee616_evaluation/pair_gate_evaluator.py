"""Evaluation-only recorder for the one-leader/one-follower Gazebo gate."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys
import time

from ee616_evaluation.pose_text import parse_entity_pose
from geometry_msgs.msg import Twist, Vector3Stamped
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String


CSV_FIELDS = [
    "elapsed_s", "profile", "route_state", "control_state",
    "true_range_m", "true_bearing_deg", "spacing_error_m",
    "estimated_range_m", "estimated_bearing_deg", "measurement_age_s",
    "follower_linear_cmd_mps", "follower_angular_cmd_rps",
    "leader_linear_cmd_mps", "leader_angular_cmd_rps",
    "center_distance_m", "collision_sample", "inference_ms",
]


def percentile(values: list[float], fraction: float) -> float | None:
    """Return a linearly interpolated percentile for finite values."""
    ordered = sorted(value for value in values if math.isfinite(value))
    if not ordered:
        return None
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


class PairGateEvaluator(Node):
    """Read Gazebo truth only here and record closed-loop pair metrics."""

    def __init__(self) -> None:
        super().__init__("pair_gate_evaluator")
        self.declare_parameter("profile", "straight")
        self.declare_parameter("run_id", "run_01")
        self.declare_parameter("output_dir", "results/pair_gate")
        self.declare_parameter("duration_s", 24.0)
        self.declare_parameter("warmup_s", 4.0)
        self.declare_parameter("desired_range_m", 1.5)
        self.declare_parameter("max_linear_mps", 0.6)
        self.declare_parameter("max_angular_rps", 0.8)
        self.profile = str(self.get_parameter("profile").value)
        self.run_id = str(self.get_parameter("run_id").value)
        self.output_dir = Path(str(self.get_parameter("output_dir").value))
        self.duration_s = float(self.get_parameter("duration_s").value)
        self.warmup_s = float(self.get_parameter("warmup_s").value)
        self.desired_range_m = float(self.get_parameter("desired_range_m").value)
        self.max_linear_mps = float(self.get_parameter("max_linear_mps").value)
        self.max_angular_rps = float(self.get_parameter("max_angular_rps").value)
        self.started = time.monotonic()
        self.rows: list[dict] = []
        self.control_periods_ms: list[float] = []
        self.last_estimate_stamp_s: float | None = None
        self.route_state = "UNSEEN"
        self.control_state = "UNSEEN"
        self.estimate = [math.nan, math.nan, math.inf]
        self.follower_command = [0.0, 0.0]
        self.leader_command = [0.0, 0.0]
        self.inference_ms: float | None = None
        self.failure = ""
        self.exit_code = 1
        self.done = False
        self.create_subscription(String, "/leader/route/state", self._route_state, 10)
        self.create_subscription(String, "/follower_1/control/state", self._control_state, 10)
        self.create_subscription(Vector3Stamped, "/follower_1/control/estimate", self._estimate, 10)
        self.create_subscription(Twist, "/follower_1/cmd_vel", self._follower_command, 10)
        self.create_subscription(Twist, "/leader/cmd_vel", self._leader_command, 10)
        self.create_subscription(Float32, "/follower_1/measurement/inference_ms", self._latency, 10)
        self.timer = self.create_timer(0.2, self._sample)

    @property
    def pose_topic(self) -> str:
        return f"/world/pair_{self.profile}/pose/info"

    def _route_state(self, message: String) -> None:
        self.route_state = message.data

    def _control_state(self, message: String) -> None:
        self.control_state = message.data

    def _estimate(self, message: Vector3Stamped) -> None:
        stamp_s = message.header.stamp.sec + message.header.stamp.nanosec * 1.0e-9
        if self.last_estimate_stamp_s is not None and stamp_s > self.last_estimate_stamp_s:
            self.control_periods_ms.append((stamp_s - self.last_estimate_stamp_s) * 1000.0)
        self.last_estimate_stamp_s = stamp_s
        self.estimate = [message.vector.x, message.vector.y, message.vector.z]

    def _follower_command(self, message: Twist) -> None:
        self.follower_command = [message.linear.x, message.angular.z]

    def _leader_command(self, message: Twist) -> None:
        self.leader_command = [message.linear.x, message.angular.z]

    def _latency(self, message: Float32) -> None:
        value = float(message.data)
        self.inference_ms = value if math.isfinite(value) else None

    def _read_poses(self):
        result = subprocess.run(
            ["gz", "topic", "-e", "-t", self.pose_topic, "-n", "1"],
            check=True,
            capture_output=True,
            text=True,
            timeout=3.0,
        )
        return (
            parse_entity_pose(result.stdout, "leader"),
            parse_entity_pose(result.stdout, "follower_1"),
        )

    def _sample(self) -> None:
        if self.done:
            return
        elapsed_s = time.monotonic() - self.started
        if elapsed_s >= self.duration_s:
            self._finish("")
            return
        try:
            leader, follower = self._read_poses()
        except (ValueError, subprocess.SubprocessError) as exc:
            if elapsed_s > 5.0:
                self._finish(f"unable to read pair ground truth: {exc}")
            return
        camera_x = follower.x + math.cos(follower.yaw) * 0.28
        camera_y = follower.y + math.sin(follower.yaw) * 0.28
        target_x = leader.x - math.cos(leader.yaw) * 0.30
        target_y = leader.y - math.sin(leader.yaw) * 0.30
        dx = target_x - camera_x
        dy = target_y - camera_y
        forward = math.cos(follower.yaw) * dx + math.sin(follower.yaw) * dy
        left = -math.sin(follower.yaw) * dx + math.cos(follower.yaw) * dy
        true_range = math.hypot(forward, left)
        center_distance = math.hypot(leader.x - follower.x, leader.y - follower.y)
        self.rows.append(
            {
                "elapsed_s": elapsed_s,
                "profile": self.profile,
                "route_state": self.route_state,
                "control_state": self.control_state,
                "true_range_m": true_range,
                "true_bearing_deg": math.degrees(math.atan2(left, forward)),
                "spacing_error_m": true_range - self.desired_range_m,
                "estimated_range_m": self.estimate[0],
                "estimated_bearing_deg": math.degrees(self.estimate[1]),
                "measurement_age_s": self.estimate[2],
                "follower_linear_cmd_mps": self.follower_command[0],
                "follower_angular_cmd_rps": self.follower_command[1],
                "leader_linear_cmd_mps": self.leader_command[0],
                "leader_angular_cmd_rps": self.leader_command[1],
                "center_distance_m": center_distance,
                "collision_sample": int(center_distance < 0.65),
                "inference_ms": self.inference_ms,
            }
        )

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
        stem = f"{self.profile}_{self.run_id}"
        with (self.output_dir / f"{stem}_samples.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(self.rows)
        evaluated = [row for row in self.rows if row["elapsed_s"] >= self.warmup_s]
        errors = [row["spacing_error_m"] for row in evaluated]
        spacing_rmse = math.sqrt(statistics.fmean(error * error for error in errors)) if errors else None
        track_fraction = (
            sum(row["control_state"] == "TRACK" for row in evaluated) / len(evaluated)
            if evaluated else 0.0
        )
        period_p95 = percentile(self.control_periods_ms, 0.95)
        bounded = all(
            0.0 <= row["follower_linear_cmd_mps"] <= self.max_linear_mps + 1.0e-6
            and abs(row["follower_angular_cmd_rps"]) <= self.max_angular_rps + 1.0e-6
            for row in self.rows
        )
        checks = {
            "spacing_rmse": spacing_rmse is not None and spacing_rmse <= 0.20,
            "collision_samples": sum(row["collision_sample"] for row in evaluated) == 0,
            "route_complete": any(row["route_state"] == "COMPLETE" for row in self.rows),
            "bounded_commands": bounded,
            "control_period_p95": period_p95 is not None and period_p95 <= 66.7,
            "track_fraction": track_fraction >= 0.95,
        }
        summary = {
            "profile": self.profile,
            "run_id": self.run_id,
            "sample_count": len(self.rows),
            "evaluated_sample_count": len(evaluated),
            "spacing_rmse_m": spacing_rmse,
            "minimum_center_distance_m": min((row["center_distance_m"] for row in evaluated), default=None),
            "collision_samples": sum(row["collision_sample"] for row in evaluated),
            "track_fraction": track_fraction,
            "safe_stop_samples": sum(row["control_state"] == "SAFE_STOP" for row in evaluated),
            "control_period_p95_ms": period_p95,
            "inference_latency_p95_ms": percentile(
                [row["inference_ms"] for row in evaluated if row["inference_ms"] is not None], 0.95
            ),
            "route_complete": checks["route_complete"],
            "bounded_commands": bounded,
            "checks": checks,
            "failure": self.failure or None,
            "status": "pass" if not self.failure and all(checks.values()) else "fail",
            "ground_truth_boundary": (
                f"Gazebo {self.pose_topic} was read only by ee616_evaluation and was not "
                "published to perception, estimation, supervision, or control."
            ),
            "scope": "One simulated leader-follower pair; not multi-follower, physical-robot, or safety evidence.",
        }
        (self.output_dir / f"{stem}_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = PairGateEvaluator()
    try:
        rclpy.spin(node)
    finally:
        exit_code = node.exit_code
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    if exit_code:
        print("Pair gate evaluator failed; see run summary.", file=sys.stderr)
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
