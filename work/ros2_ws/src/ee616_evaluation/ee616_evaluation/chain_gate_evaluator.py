"""Evaluation-only recorder for incremental two- and three-follower gates."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys
import time

from ee616_evaluation.pair_gate_evaluator import percentile
from ee616_evaluation.pose_text import parse_entity_pose
from geometry_msgs.msg import Twist, Vector3Stamped
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String


CSV_FIELDS = [
    "elapsed_s", "profile", "follower_count", "follower_index", "predecessor",
    "route_state", "control_state", "true_range_m", "true_bearing_deg",
    "spacing_error_m", "estimated_range_m", "estimated_bearing_deg",
    "measurement_age_s", "linear_cmd_mps", "angular_cmd_rps",
    "center_distance_m", "collision_sample", "inference_ms",
]


class ChainGateEvaluator(Node):
    """Read simulator truth only for metrics; never republish it to the stack."""

    def __init__(self) -> None:
        super().__init__("chain_gate_evaluator")
        self.declare_parameter("profile", "straight")
        self.declare_parameter("follower_count", 2)
        self.declare_parameter("run_id", "run_01")
        self.declare_parameter("output_dir", "results/chain_gate")
        self.declare_parameter("duration_s", 24.0)
        self.declare_parameter("warmup_s", 4.0)
        self.declare_parameter("desired_range_m", 1.5)
        self.declare_parameter("max_linear_mps", 0.6)
        self.declare_parameter("max_angular_rps", 0.8)
        self.profile = str(self.get_parameter("profile").value)
        self.follower_count = int(self.get_parameter("follower_count").value)
        if self.follower_count not in {2, 3}:
            raise ValueError("follower_count must be 2 or 3")
        self.run_id = str(self.get_parameter("run_id").value)
        self.output_dir = Path(str(self.get_parameter("output_dir").value))
        self.duration_s = float(self.get_parameter("duration_s").value)
        self.warmup_s = float(self.get_parameter("warmup_s").value)
        self.desired_range_m = float(self.get_parameter("desired_range_m").value)
        self.max_linear_mps = float(self.get_parameter("max_linear_mps").value)
        self.max_angular_rps = float(self.get_parameter("max_angular_rps").value)
        self.started = time.monotonic()
        self.rows: list[dict] = []
        indexes = range(1, self.follower_count + 1)
        self.control_states = {index: "UNSEEN" for index in indexes}
        self.estimates = {index: [math.nan, math.nan, math.inf] for index in indexes}
        self.commands = {index: [0.0, 0.0] for index in indexes}
        self.inference_ms = {index: None for index in indexes}
        self.last_estimate_stamp_s = {index: None for index in indexes}
        self.control_periods_ms = {index: [] for index in indexes}
        self.route_state = "UNSEEN"
        self.failure = ""
        self.exit_code = 1
        self.done = False
        self.create_subscription(String, "/leader/route/state", self._route_state, 10)
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
        return f"/world/chain_{self.follower_count}_{self.profile}/pose/info"

    def _route_state(self, message: String) -> None:
        self.route_state = message.data

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
        result = subprocess.run(
            ["gz", "topic", "-e", "-t", self.pose_topic, "-n", "1"],
            check=True, capture_output=True, text=True, timeout=3.0,
        )
        names = ["leader"] + [f"follower_{index}" for index in range(1, self.follower_count + 1)]
        return {name: parse_entity_pose(result.stdout, name) for name in names}

    def _sample(self) -> None:
        if self.done:
            return
        elapsed_s = time.monotonic() - self.started
        if elapsed_s >= self.duration_s:
            self._finish("")
            return
        try:
            poses = self._read_poses()
        except (ValueError, subprocess.SubprocessError) as exc:
            if elapsed_s > 5.0:
                self._finish(f"unable to read chain ground truth: {exc}")
            return
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
            center_distance = math.hypot(predecessor.x - follower.x, predecessor.y - follower.y)
            estimate = self.estimates[index]
            command = self.commands[index]
            self.rows.append({
                "elapsed_s": elapsed_s,
                "profile": self.profile,
                "follower_count": self.follower_count,
                "follower_index": index,
                "predecessor": predecessor_name,
                "route_state": self.route_state,
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
        stem = f"chain_{self.follower_count}_{self.profile}_{self.run_id}"
        with (self.output_dir / f"{stem}_samples.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(self.rows)
        followers = {}
        all_checks = []
        for index in range(1, self.follower_count + 1):
            evaluated = [
                row for row in self.rows
                if row["follower_index"] == index and row["elapsed_s"] >= self.warmup_s
            ]
            errors = [row["spacing_error_m"] for row in evaluated]
            rmse = math.sqrt(statistics.fmean(error * error for error in errors)) if errors else None
            track_fraction = (
                sum(row["control_state"] == "TRACK" for row in evaluated) / len(evaluated)
                if evaluated else 0.0
            )
            period_p95 = percentile(self.control_periods_ms[index], 0.95)
            bounded = all(
                0.0 <= row["linear_cmd_mps"] <= self.max_linear_mps + 1.0e-6
                and abs(row["angular_cmd_rps"]) <= self.max_angular_rps + 1.0e-6
                for row in evaluated
            )
            checks = {
                "spacing_rmse": rmse is not None and rmse <= (0.20 if index == 1 else 0.25),
                "collision_samples": sum(row["collision_sample"] for row in evaluated) == 0,
                "bounded_commands": bounded,
                "control_period_p95": period_p95 is not None and period_p95 <= 66.7,
                "track_fraction": track_fraction >= 0.95,
            }
            all_checks.extend(checks.values())
            followers[str(index)] = {
                "predecessor": "leader" if index == 1 else f"follower_{index - 1}",
                "spacing_rmse_m": rmse,
                "minimum_center_distance_m": min((row["center_distance_m"] for row in evaluated), default=None),
                "collision_samples": sum(row["collision_sample"] for row in evaluated),
                "track_fraction": track_fraction,
                "safe_stop_samples": sum(row["control_state"] == "SAFE_STOP" for row in evaluated),
                "control_period_p95_ms": period_p95,
                "inference_latency_p95_ms": percentile(
                    [row["inference_ms"] for row in evaluated if row["inference_ms"] is not None], 0.95
                ),
                "bounded_commands": bounded,
                "checks": checks,
            }
        route_complete = any(row["route_state"] == "COMPLETE" for row in self.rows)
        rmse_sequence = [followers[str(index)]["spacing_rmse_m"] for index in range(1, self.follower_count + 1)]
        summary = {
            "profile": self.profile,
            "follower_count": self.follower_count,
            "run_id": self.run_id,
            "sample_count": len(self.rows),
            "followers": followers,
            "rearward_rmse_delta_m": [
                rmse_sequence[index] - rmse_sequence[index - 1]
                for index in range(1, len(rmse_sequence))
            ],
            "route_complete": route_complete,
            "failure": self.failure or None,
            "status": "pass" if not self.failure and route_complete and all(all_checks) else "fail",
            "ground_truth_boundary": (
                f"Gazebo {self.pose_topic} was read only by ee616_evaluation and was not "
                "published to perception, estimation, supervision, or control."
            ),
            "scope": "Nominal simulated incremental chain; not disturbance, physical-robot, or safety evidence.",
        }
        (self.output_dir / f"{stem}_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ChainGateEvaluator()
    try:
        rclpy.spin(node)
    finally:
        exit_code = node.exit_code
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    if exit_code:
        print("Chain gate evaluator failed; see run summary.", file=sys.stderr)
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
