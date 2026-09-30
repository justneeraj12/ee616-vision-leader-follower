"""Evaluation-only observer for Gate 6 timing measurements."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import statistics
import sys
import time

from ee616_evaluation.pair_gate_evaluator import percentile
from geometry_msgs.msg import Twist, Vector3Stamped
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import Float32, String


CSV_FIELDS = [
    "wall_elapsed_s", "sim_time_s", "follower_index", "stage",
    "source_stamp_s", "latency_ms", "valid_measurement",
]


def latency_summary(values: list[float]) -> dict:
    finite = [value for value in values if math.isfinite(value) and value >= 0.0]
    return {
        "count": len(finite),
        "mean_ms": statistics.fmean(finite) if finite else None,
        "p50_ms": percentile(finite, 0.50),
        "p95_ms": percentile(finite, 0.95),
        "p99_ms": percentile(finite, 0.99),
        "max_ms": max(finite) if finite else None,
    }


def stamped_rate_hz(stamps_s: list[float]) -> float | None:
    ordered = sorted(set(stamps_s))
    if len(ordered) < 2 or ordered[-1] <= ordered[0]:
        return None
    return (len(ordered) - 1) / (ordered[-1] - ordered[0])


def _stamp_s(message) -> float:
    return message.header.stamp.sec + message.header.stamp.nanosec * 1.0e-9


class TimingGateEvaluator(Node):
    """Observe pipeline timing without publishing into the robot stack."""

    def __init__(self) -> None:
        super().__init__("timing_gate_evaluator")
        self.declare_parameter("follower_count", 3)
        self.declare_parameter("run_id", "run_01")
        self.declare_parameter("output_dir", "results/timing_gate")
        self.declare_parameter("duration_s", 49.0)
        self.declare_parameter("warmup_s", 8.0)
        self.follower_count = int(self.get_parameter("follower_count").value)
        if self.follower_count != 3:
            raise ValueError("Gate 6 uses the accepted three-follower configuration")
        self.run_id = str(self.get_parameter("run_id").value)
        self.output_dir = Path(str(self.get_parameter("output_dir").value))
        self.duration_s = float(self.get_parameter("duration_s").value)
        self.warmup_s = float(self.get_parameter("warmup_s").value)
        self.started_ns = time.monotonic_ns()
        indexes = range(1, self.follower_count + 1)
        self.rows: list[dict] = []
        self.camera_arrivals = {index: {} for index in indexes}
        self.pending_measurements = {index: None for index in indexes}
        self.pending_controller_commands = {index: None for index in indexes}
        self.camera_stamps = {index: [] for index in indexes}
        self.measurement_stamps = {index: [] for index in indexes}
        self.valid_measurements = {index: 0 for index in indexes}
        self.latencies = {
            index: {
                "camera_to_measurement": [],
                "measurement_to_controller_cmd": [],
                "controller_to_actual_cmd": [],
                "detector_inference": [],
                "control_period": [],
            }
            for index in indexes
        }
        self.last_estimate_stamp = {index: None for index in indexes}
        self.route_complete = False
        self.sim_first_s = None
        self.sim_last_s = None
        self.rtf_wall_first_ns = None
        self.rtf_wall_last_ns = None
        self.done = False
        self.failure = ""
        self.exit_code = 1
        self.create_subscription(String, "/leader/route/state", self._route_state, 10)
        for index in indexes:
            prefix = f"/follower_{index}"
            self.create_subscription(
                Image,
                f"{prefix}/camera/disturbed",
                lambda message, i=index: self._camera(i, message),
                qos_profile_sensor_data,
            )
            self.create_subscription(
                Vector3Stamped,
                f"{prefix}/measurement/relative",
                lambda message, i=index: self._measurement(i, message),
                10,
            )
            self.create_subscription(
                Float32,
                f"{prefix}/measurement/inference_ms",
                lambda message, i=index: self._inference(i, message),
                10,
            )
            self.create_subscription(
                Twist,
                f"{prefix}/controller_cmd_vel",
                lambda message, i=index: self._controller_command(i, message),
                10,
            )
            self.create_subscription(
                Twist,
                f"{prefix}/cmd_vel",
                lambda message, i=index: self._actual_command(i, message),
                10,
            )
            self.create_subscription(
                Vector3Stamped,
                f"{prefix}/control/estimate",
                lambda message, i=index: self._estimate(i, message),
                10,
            )
        self.timer = self.create_timer(0.1, self._tick)

    def _elapsed_s(self, now_ns: int | None = None) -> float:
        return ((now_ns or time.monotonic_ns()) - self.started_ns) * 1.0e-9

    def _record(
        self,
        index: int,
        stage: str,
        latency_ms: float,
        *,
        source_stamp_s: float | None = None,
        valid: bool | None = None,
        now_ns: int | None = None,
    ) -> None:
        now_ns = now_ns or time.monotonic_ns()
        self.latencies[index][stage].append(latency_ms)
        self.rows.append({
            "wall_elapsed_s": self._elapsed_s(now_ns),
            "sim_time_s": self.get_clock().now().nanoseconds * 1.0e-9,
            "follower_index": index,
            "stage": stage,
            "source_stamp_s": source_stamp_s,
            "latency_ms": latency_ms,
            "valid_measurement": valid,
        })

    def _route_state(self, message: String) -> None:
        self.route_complete = self.route_complete or message.data == "COMPLETE"

    def _camera(self, index: int, message: Image) -> None:
        now_ns = time.monotonic_ns()
        stamp = _stamp_s(message)
        self.camera_stamps[index].append(stamp)
        arrivals = self.camera_arrivals[index]
        arrivals[stamp] = now_ns
        if len(arrivals) > 120:
            for old_stamp in sorted(arrivals)[:-100]:
                arrivals.pop(old_stamp, None)

    def _measurement(self, index: int, message: Vector3Stamped) -> None:
        now_ns = time.monotonic_ns()
        stamp = _stamp_s(message)
        self.measurement_stamps[index].append(stamp)
        arrival_ns = self.camera_arrivals[index].pop(stamp, None)
        valid = message.vector.z >= 0.5
        if arrival_ns is not None and now_ns >= arrival_ns:
            self._record(
                index,
                "camera_to_measurement",
                (now_ns - arrival_ns) * 1.0e-6,
                source_stamp_s=stamp,
                valid=valid,
                now_ns=now_ns,
            )
        if valid:
            self.valid_measurements[index] += 1
            self.pending_measurements[index] = now_ns

    def _inference(self, index: int, message: Float32) -> None:
        value = float(message.data)
        if math.isfinite(value) and value >= 0.0:
            self._record(index, "detector_inference", value)

    def _controller_command(self, index: int, _message: Twist) -> None:
        now_ns = time.monotonic_ns()
        measurement_ns = self.pending_measurements[index]
        if measurement_ns is not None and now_ns >= measurement_ns:
            self._record(
                index,
                "measurement_to_controller_cmd",
                (now_ns - measurement_ns) * 1.0e-6,
                valid=True,
                now_ns=now_ns,
            )
            self.pending_measurements[index] = None
        self.pending_controller_commands[index] = now_ns

    def _actual_command(self, index: int, _message: Twist) -> None:
        now_ns = time.monotonic_ns()
        controller_ns = self.pending_controller_commands[index]
        if controller_ns is not None and now_ns >= controller_ns:
            self._record(
                index,
                "controller_to_actual_cmd",
                (now_ns - controller_ns) * 1.0e-6,
                now_ns=now_ns,
            )
            self.pending_controller_commands[index] = None

    def _estimate(self, index: int, message: Vector3Stamped) -> None:
        stamp = _stamp_s(message)
        previous = self.last_estimate_stamp[index]
        if previous is not None and stamp > previous:
            self._record(
                index,
                "control_period",
                (stamp - previous) * 1000.0,
                source_stamp_s=stamp,
            )
        self.last_estimate_stamp[index] = stamp

    def _tick(self) -> None:
        if self.done:
            return
        now_ns = time.monotonic_ns()
        elapsed = self._elapsed_s(now_ns)
        if elapsed >= self.warmup_s:
            sim_s = self.get_clock().now().nanoseconds * 1.0e-9
            if self.sim_first_s is None:
                self.sim_first_s = sim_s
                self.rtf_wall_first_ns = now_ns
            self.sim_last_s = sim_s
            self.rtf_wall_last_ns = now_ns
        if elapsed >= self.duration_s:
            self._finish("")

    def _real_time_factor(self) -> float | None:
        if (
            self.sim_first_s is None
            or self.sim_last_s is None
            or self.rtf_wall_first_ns is None
            or self.rtf_wall_last_ns is None
            or self.rtf_wall_last_ns <= self.rtf_wall_first_ns
        ):
            return None
        wall_s = (self.rtf_wall_last_ns - self.rtf_wall_first_ns) * 1.0e-9
        return (self.sim_last_s - self.sim_first_s) / wall_s

    def _finish(self, failure: str) -> None:
        if self.done:
            return
        self.done = True
        self.failure = failure
        self._write_results()
        self.exit_code = 0 if not failure else 1
        if failure:
            self.get_logger().error(failure)
        if rclpy.ok():
            rclpy.shutdown()

    def _write_results(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        stem = f"timing_3_combined_{self.run_id}"
        with (self.output_dir / f"{stem}_samples.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(self.rows)
        followers = {}
        all_checks = []
        for index in range(1, self.follower_count + 1):
            summaries = {
                stage: latency_summary(values)
                for stage, values in self.latencies[index].items()
            }
            camera_count = len(self.camera_stamps[index])
            measurement_count = len(self.measurement_stamps[index])
            delivery_ratio = measurement_count / camera_count if camera_count else 0.0
            checks = {
                "camera_to_measurement_p95": (
                    summaries["camera_to_measurement"]["p95_ms"] is not None
                    and summaries["camera_to_measurement"]["p95_ms"] <= 66.7
                ),
                "measurement_to_controller_cmd_p95": (
                    summaries["measurement_to_controller_cmd"]["p95_ms"] is not None
                    and summaries["measurement_to_controller_cmd"]["p95_ms"] <= 66.7
                ),
                "controller_to_actual_cmd_p95": (
                    summaries["controller_to_actual_cmd"]["p95_ms"] is not None
                    and summaries["controller_to_actual_cmd"]["p95_ms"] <= 50.0
                ),
                "detector_inference_p95": (
                    summaries["detector_inference"]["p95_ms"] is not None
                    and summaries["detector_inference"]["p95_ms"] <= 66.7
                ),
                "control_period_p95": (
                    summaries["control_period"]["p95_ms"] is not None
                    and summaries["control_period"]["p95_ms"] <= 66.7
                ),
                "measurement_delivery_ratio": delivery_ratio >= 0.95,
            }
            all_checks.extend(checks.values())
            followers[str(index)] = {
                "camera_message_count": camera_count,
                "camera_rate_hz": stamped_rate_hz(self.camera_stamps[index]),
                "measurement_message_count": measurement_count,
                "measurement_rate_hz": stamped_rate_hz(self.measurement_stamps[index]),
                "measurement_delivery_ratio": delivery_ratio,
                "valid_measurement_count": self.valid_measurements[index],
                "latency": summaries,
                "checks": checks,
            }
        rtf = self._real_time_factor()
        run_checks = {
            "route_complete": self.route_complete,
            "real_time_factor": rtf is not None and rtf >= 0.90,
        }
        all_checks.extend(run_checks.values())
        summary = {
            "run_id": self.run_id,
            "scenario": "combined",
            "follower_count": self.follower_count,
            "duration_s": self.duration_s,
            "warmup_s": self.warmup_s,
            "followers": followers,
            "real_time_factor": rtf,
            "run_checks": run_checks,
            "failure": self.failure or None,
            "status": "pass" if not self.failure and all(all_checks) else "fail",
            "measurement_note": (
                "Camera-to-measurement and command-stage values are observer-side "
                "wall-clock estimates on one host; detector inference is reported "
                "directly by the perception node."
            ),
            "ground_truth_boundary": (
                "This timing evaluator did not subscribe to Gazebo pose truth or "
                "publish into perception, estimation, supervision, or control."
            ),
            "scope": "Target-laptop simulation timing; not networked or physical-robot timing.",
        }
        (self.output_dir / f"{stem}_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TimingGateEvaluator()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if not node.done:
            node._finish("timing observer interrupted before its measurement duration completed")
        exit_code = node.exit_code
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    if exit_code:
        print("Timing evaluator failed; see run summary.", file=sys.stderr)
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
