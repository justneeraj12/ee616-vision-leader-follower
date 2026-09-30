"""Evaluation-only recorder for controlled visual and motion disturbances."""

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
    "elapsed_s", "scenario", "follower_count", "follower_index", "predecessor",
    "route_state", "event", "control_state", "true_range_m", "true_bearing_deg",
    "spacing_error_m", "estimated_range_m", "estimated_bearing_deg",
    "measurement_age_s", "linear_cmd_mps", "angular_cmd_rps",
    "center_distance_m", "collision_sample", "inference_ms",
]

POSE_READ_ATTEMPTS = 3
CONSECUTIVE_POSE_FAILURE_LIMIT = 3


def _read_with_retries(read_once, attempts: int = POSE_READ_ATTEMPTS):
    """Retry transient Gazebo CLI failures without accepting missing truth data."""
    if attempts < 1:
        raise ValueError("attempts must be at least one")
    last_error = None
    for attempt in range(attempts):
        try:
            return read_once()
        except (ValueError, subprocess.SubprocessError) as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(0.05)
    raise RuntimeError(f"Gazebo pose read failed after {attempts} attempts: {last_error}") from last_error


def _event_metrics(rows: list[dict], label: str) -> dict:
    event_rows = [row for row in rows if row["event"] == label]
    if not event_rows:
        return {
            "observed": False,
            "predict_observed": False,
            "safe_stop_observed": False,
            "safe_stop_latency_s": None,
            "track_reacquisition_s": None,
            "zero_command_during_safe_stop": False,
            "spacing_recovery_s": None,
        }
    start_s = min(row["elapsed_s"] for row in event_rows)
    end_s = max(row["elapsed_s"] for row in event_rows)
    safe_rows = [row for row in event_rows if row["control_state"] == "SAFE_STOP"]
    future = [row for row in rows if row["elapsed_s"] > end_s and row["event"] == "NONE"]
    track_rows = [row for row in future if row["control_state"] == "TRACK"]
    recovered = [row for row in future if abs(row["spacing_error_m"]) <= 0.20]
    return {
        "observed": True,
        "predict_observed": any(row["control_state"] == "PREDICT" for row in event_rows),
        "safe_stop_observed": bool(safe_rows),
        "safe_stop_latency_s": min((row["elapsed_s"] - start_s for row in safe_rows), default=None),
        "track_reacquisition_s": min((row["elapsed_s"] - end_s for row in track_rows), default=None),
        "zero_command_during_safe_stop": bool(safe_rows) and all(
            abs(row["linear_cmd_mps"]) <= 1.0e-6
            and abs(row["angular_cmd_rps"]) <= 1.0e-6
            for row in safe_rows
        ),
        "spacing_recovery_s": min((row["elapsed_s"] - end_s for row in recovered), default=None),
    }


def _stop_metrics(rows: list[dict]) -> dict:
    stopped = [row for row in rows if row["route_state"] == "STOPPED"]
    if not stopped:
        return {
            "observed": False,
            "final_linear_cmd_mps": None,
            "final_angular_cmd_rps": None,
            "final_spacing_error_m": None,
        }
    final = stopped[-1]
    return {
        "observed": True,
        "final_linear_cmd_mps": final["linear_cmd_mps"],
        "final_angular_cmd_rps": final["angular_cmd_rps"],
        "final_spacing_error_m": final["spacing_error_m"],
    }


def _stop_settled(rows: list[dict]) -> bool:
    metrics = _stop_metrics(rows)
    return (
        metrics["observed"]
        and abs(metrics["final_linear_cmd_mps"]) <= 0.08
        and abs(metrics["final_angular_cmd_rps"]) <= 0.08
    )


def _turn_recovered(rows: list[dict]) -> bool:
    if not any(row["route_state"] == "TURN_HARD" for row in rows):
        return False
    straight = [row for row in rows if row["route_state"] in {"STRAIGHT_2", "STRAIGHT_3"}]
    tail = straight[-10:]
    return bool(tail) and statistics.fmean(abs(row["spacing_error_m"]) for row in tail) <= 0.20


class DisturbanceGateEvaluator(Node):
    """Measure recovery while keeping Gazebo truth outside the robot stack."""

    def __init__(self) -> None:
        super().__init__("disturbance_gate_evaluator")
        self.declare_parameter("scenario", "short_occlusion")
        self.declare_parameter("follower_count", 1)
        self.declare_parameter("target_follower", 1)
        self.declare_parameter("run_id", "run_01")
        self.declare_parameter("output_dir", "results/disturbance_gate")
        self.declare_parameter("duration_s", 24.0)
        self.declare_parameter("warmup_s", 4.0)
        self.declare_parameter("desired_range_m", 1.5)
        self.declare_parameter("max_linear_mps", 0.6)
        self.declare_parameter("max_angular_rps", 0.8)
        self.scenario = str(self.get_parameter("scenario").value)
        self.follower_count = int(self.get_parameter("follower_count").value)
        self.target_follower = int(self.get_parameter("target_follower").value)
        if self.follower_count not in {1, 3}:
            raise ValueError("follower_count must be 1 or 3")
        if not 1 <= self.target_follower <= self.follower_count:
            raise ValueError("target_follower is outside the chain")
        self.run_id = str(self.get_parameter("run_id").value)
        self.output_dir = Path(str(self.get_parameter("output_dir").value))
        self.duration_s = float(self.get_parameter("duration_s").value)
        self.warmup_s = float(self.get_parameter("warmup_s").value)
        self.desired_range_m = float(self.get_parameter("desired_range_m").value)
        self.max_linear_mps = float(self.get_parameter("max_linear_mps").value)
        self.max_angular_rps = float(self.get_parameter("max_angular_rps").value)
        self.started = time.monotonic()
        indexes = range(1, self.follower_count + 1)
        self.rows: list[dict] = []
        self.route_state = "UNSEEN"
        self.event = "NONE"
        self.control_states = {index: "UNSEEN" for index in indexes}
        self.estimates = {index: [math.nan, math.nan, math.inf] for index in indexes}
        self.commands = {index: [0.0, 0.0] for index in indexes}
        self.inference_ms = {index: None for index in indexes}
        self.last_estimate_stamp_s = {index: None for index in indexes}
        self.control_periods_ms = {index: [] for index in indexes}
        self.failure = ""
        self.pose_read_failure_count = 0
        self.consecutive_pose_failures = 0
        self.exit_code = 1
        self.done = False
        self.create_subscription(String, "/leader/route/state", self._route_state, 10)
        self.create_subscription(String, "/experiment/event", self._event, 10)
        for index in indexes:
            prefix = f"/follower_{index}"
            self.create_subscription(String, f"{prefix}/control/state", lambda message, i=index: self._state(i, message), 10)
            self.create_subscription(Vector3Stamped, f"{prefix}/control/estimate", lambda message, i=index: self._estimate(i, message), 10)
            self.create_subscription(Twist, f"{prefix}/cmd_vel", lambda message, i=index: self._command(i, message), 10)
            self.create_subscription(Float32, f"{prefix}/measurement/inference_ms", lambda message, i=index: self._latency(i, message), 10)
        self.timer = self.create_timer(0.2, self._sample)

    @property
    def pose_topic(self) -> str:
        return f"/world/disturbance_{self.follower_count}_{self.scenario}/pose/info"

    def _route_state(self, message: String) -> None:
        self.route_state = message.data

    def _event(self, message: String) -> None:
        self.event = message.data

    def _state(self, index: int, message: String) -> None:
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
        def read_once() -> dict:
            result = subprocess.run(
                ["gz", "topic", "-e", "-t", self.pose_topic, "-n", "1"],
                check=True, capture_output=True, text=True, timeout=3.0,
            )
            names = ["leader"] + [
                f"follower_{index}" for index in range(1, self.follower_count + 1)
            ]
            return {name: parse_entity_pose(result.stdout, name) for name in names}

        return _read_with_retries(read_once)

    def _sample(self) -> None:
        if self.done:
            return
        elapsed_s = time.monotonic() - self.started
        if elapsed_s >= self.duration_s:
            self._finish("")
            return
        try:
            poses = self._read_poses()
        except (RuntimeError, ValueError, subprocess.SubprocessError) as exc:
            self.pose_read_failure_count += 1
            self.consecutive_pose_failures += 1
            self.get_logger().warning(
                "disturbance ground-truth read failed "
                f"({self.consecutive_pose_failures}/{CONSECUTIVE_POSE_FAILURE_LIMIT}): {exc}"
            )
            if (
                elapsed_s > 5.0
                and self.consecutive_pose_failures >= CONSECUTIVE_POSE_FAILURE_LIMIT
            ):
                self._finish(f"unable to read disturbance ground truth: {exc}")
            return
        self.consecutive_pose_failures = 0
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
                "scenario": self.scenario,
                "follower_count": self.follower_count,
                "follower_index": index,
                "predecessor": predecessor_name,
                "route_state": self.route_state,
                "event": self.event,
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
        stem = f"disturbance_{self.follower_count}_{self.scenario}_{self.run_id}"
        with (self.output_dir / f"{stem}_samples.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(self.rows)
        followers = {}
        general_checks = []
        follower_rows = {}
        for index in range(1, self.follower_count + 1):
            evaluated = [row for row in self.rows if row["follower_index"] == index and row["elapsed_s"] >= self.warmup_s]
            follower_rows[index] = evaluated
            errors = [row["spacing_error_m"] for row in evaluated]
            rmse = math.sqrt(statistics.fmean(error * error for error in errors)) if errors else None
            track_fraction = sum(row["control_state"] == "TRACK" for row in evaluated) / len(evaluated) if evaluated else 0.0
            bounded = all(
                0.0 <= row["linear_cmd_mps"] <= self.max_linear_mps + 1.0e-6
                and abs(row["angular_cmd_rps"]) <= self.max_angular_rps + 1.0e-6
                for row in evaluated
            )
            checks = {
                "disturbed_spacing_rmse": rmse is not None and rmse <= (0.30 if index == 1 else 0.35),
                "collision_samples": sum(row["collision_sample"] for row in evaluated) == 0,
                "bounded_actual_commands": bounded,
                "control_period_p95": (
                    percentile(self.control_periods_ms[index], 0.95) is not None
                    and percentile(self.control_periods_ms[index], 0.95) <= 66.7
                ),
                "track_fraction": track_fraction >= 0.85,
            }
            general_checks.extend(checks.values())
            followers[str(index)] = {
                "predecessor": "leader" if index == 1 else f"follower_{index - 1}",
                "spacing_rmse_m": rmse,
                "minimum_center_distance_m": min((row["center_distance_m"] for row in evaluated), default=None),
                "collision_samples": sum(row["collision_sample"] for row in evaluated),
                "track_fraction": track_fraction,
                "predict_samples": sum(row["control_state"] == "PREDICT" for row in evaluated),
                "safe_stop_samples": sum(row["control_state"] == "SAFE_STOP" for row in evaluated),
                "control_period_p95_ms": percentile(self.control_periods_ms[index], 0.95),
                "inference_latency_p95_ms": percentile(
                    [row["inference_ms"] for row in evaluated if row["inference_ms"] is not None], 0.95
                ),
                "checks": checks,
            }
        target_rows = follower_rows[self.target_follower]
        short = _event_metrics(target_rows, "SHORT_OCCLUSION")
        long = _event_metrics(target_rows, "LONG_OCCLUSION")
        bias = _event_metrics(target_rows, "ACTUATOR_BIAS")
        scenario_checks = {}
        if self.scenario in {"short_occlusion", "combined"}:
            scenario_checks.update({
                "short_occlusion_observed": short["observed"],
                "short_predict_observed": short["predict_observed"],
                "short_no_safe_stop": not short["safe_stop_observed"],
                "short_track_reacquisition": short["track_reacquisition_s"] is not None and short["track_reacquisition_s"] <= 0.70,
            })
        if self.scenario in {"long_occlusion", "combined"}:
            scenario_checks.update({
                "long_occlusion_observed": long["observed"],
                "long_predict_observed": long["predict_observed"],
                "long_safe_stop_observed": long["safe_stop_observed"],
                "long_safe_stop_latency": long["safe_stop_latency_s"] is not None and long["safe_stop_latency_s"] <= 1.10,
                "long_zero_command": long["zero_command_during_safe_stop"],
                "long_track_reacquisition": long["track_reacquisition_s"] is not None and long["track_reacquisition_s"] <= 0.70,
            })
        if self.scenario in {"actuator_bias", "combined"}:
            scenario_checks.update({
                "actuator_bias_observed": bias["observed"],
                "actuator_spacing_recovery": bias["spacing_recovery_s"] is not None and bias["spacing_recovery_s"] <= 3.0,
            })
        if self.scenario in {"sharp_turn", "combined"}:
            scenario_checks["sharp_turn_recovered"] = all(_turn_recovered(rows) for rows in follower_rows.values())
        if self.scenario in {"leader_stop", "combined"}:
            scenario_checks["stopped_leader_settled"] = all(_stop_settled(rows) for rows in follower_rows.values())
        route_complete = any(row["route_state"] == "COMPLETE" for row in self.rows)
        summary = {
            "scenario": self.scenario,
            "follower_count": self.follower_count,
            "target_follower": self.target_follower,
            "run_id": self.run_id,
            "sample_count": len(self.rows),
            "ground_truth_read_failures": {
                "total_failed_samples": self.pose_read_failure_count,
                "consecutive_failure_limit": CONSECUTIVE_POSE_FAILURE_LIMIT,
                "attempts_per_sample": POSE_READ_ATTEMPTS,
            },
            "followers": followers,
            "event_metrics": {"short_occlusion": short, "long_occlusion": long, "actuator_bias": bias},
            "stopped_leader_metrics": {
                str(index): _stop_metrics(rows) for index, rows in follower_rows.items()
            },
            "scenario_checks": scenario_checks,
            "route_complete": route_complete,
            "failure": self.failure or None,
            "status": "pass" if not self.failure and route_complete and all(general_checks) and all(scenario_checks.values()) else "fail",
            "ground_truth_boundary": (
                f"Gazebo {self.pose_topic} was read only by ee616_evaluation and was not "
                "published to perception, estimation, supervision, control, or the disturbance proxy."
            ),
            "scope": "Controlled simulated disturbances; not physical-robot, person-safety, or production evidence.",
        }
        (self.output_dir / f"{stem}_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = DisturbanceGateEvaluator()
    try:
        rclpy.spin(node)
    finally:
        exit_code = node.exit_code
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    if exit_code:
        print("Disturbance evaluator failed; see run summary.", file=sys.stderr)
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
