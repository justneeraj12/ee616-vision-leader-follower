"""Evaluation-only range and bearing sweep using Gazebo ground truth."""

from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from ee616_evaluation.metrics import summarize_rows
from ee616_evaluation.pose_text import EntityPose, parse_entity_pose
from ee616_evaluation.visibility import line_blocked

from geometry_msgs.msg import Vector3Stamped
import rclpy
from rclpy.node import Node


CSV_FIELDS = [
    "scene",
    "condition_id",
    "requested_range_m",
    "requested_bearing_deg",
    "actual_range_m",
    "actual_bearing_deg",
    "measured_range_m",
    "measured_bearing_deg",
    "valid",
    "full_visibility",
    "range_error_m",
    "bearing_error_deg",
    "stamp_sec",
    "stamp_nanosec",
]


class CameraGateEvaluator(Node):
    """Move the target, read measurements, and keep ground truth isolated."""

    def __init__(self) -> None:
        super().__init__("camera_gate_evaluator")
        self.declare_parameter("scene", "camera_calibration")
        self.declare_parameter(
            "measurement_topic",
            "/follower_1/measurement/relative",
        )
        self.declare_parameter("output_dir", "results/camera_measurement_gate")
        self.declare_parameter("frames_per_condition", 30)
        self.declare_parameter("settle_frames", 5)
        self.declare_parameter("timeout_s", 180.0)
        self.declare_parameter("ranges_m", [1.0, 1.5, 2.0, 3.0, 4.0, 5.0])
        self.declare_parameter(
            "bearings_deg",
            [-30.0, -20.0, -10.0, 0.0, 10.0, 20.0, 30.0],
        )
        self.declare_parameter("horizontal_fov_rad", 1.2217304764)
        self.declare_parameter("image_width", 640)
        self.declare_parameter("image_height", 480)
        self.declare_parameter("target_size", [0.08, 0.7, 0.9])
        self.declare_parameter("target_z", 0.6)
        self.declare_parameter("target_yaw", 0.0)
        self.declare_parameter("obstacles_xy_json", "[]")

        self.scene = str(self.get_parameter("scene").value)
        measurement_topic = str(
            self.get_parameter("measurement_topic").value
        )
        self.output_dir = Path(str(self.get_parameter("output_dir").value))
        self.frames_per_condition = int(
            self.get_parameter("frames_per_condition").value
        )
        self.settle_frames = int(self.get_parameter("settle_frames").value)
        self.timeout_s = float(self.get_parameter("timeout_s").value)
        ranges = [float(value) for value in self.get_parameter("ranges_m").value]
        bearings = [
            float(value) for value in self.get_parameter("bearings_deg").value
        ]
        self.conditions = [
            (range_m, bearing_deg)
            for range_m in ranges
            for bearing_deg in bearings
        ]
        self.horizontal_fov_rad = float(
            self.get_parameter("horizontal_fov_rad").value
        )
        self.image_width = int(self.get_parameter("image_width").value)
        self.image_height = int(self.get_parameter("image_height").value)
        self.target_size = tuple(
            float(value) for value in self.get_parameter("target_size").value
        )
        self.target_z = float(self.get_parameter("target_z").value)
        self.target_yaw = float(self.get_parameter("target_yaw").value)
        obstacle_values = json.loads(
            str(self.get_parameter("obstacles_xy_json").value)
        )
        self.obstacles = [
            tuple(float(value) for value in obstacle) for obstacle in obstacle_values
        ]

        self.subscription = self.create_subscription(
            Vector3Stamped,
            measurement_topic,
            self._receive_measurement,
            10,
        )
        self.timer = self.create_timer(0.1, self._tick)
        self.started = time.monotonic()
        self.phase = "waiting"
        self.received_any = False
        self.condition_index = -1
        self.settle_remaining = 0
        self.condition_rows: list[dict[str, Any]] = []
        self.rows: list[dict[str, Any]] = []
        self.actual_camera: EntityPose | None = None
        self.actual_target: EntityPose | None = None
        self.failure = ""
        self.done = False
        self.exit_code = 1

    @property
    def pose_topic(self) -> str:
        return f"/world/{self.scene}/pose/info"

    @property
    def pose_service(self) -> str:
        return f"/world/{self.scene}/set_pose"

    def _tick(self) -> None:
        if self.done:
            return
        if time.monotonic() - self.started > self.timeout_s:
            self._finish(f"experiment timed out during phase {self.phase}")
            return
        if self.phase == "waiting" and self.received_any:
            self._start_next_condition()
        elif self.phase == "advance":
            self._start_next_condition()

    def _receive_measurement(self, message: Vector3Stamped) -> None:
        self.received_any = True
        if self.phase == "settle":
            self.settle_remaining -= 1
            if self.settle_remaining <= 0:
                self.phase = "collect"
            return
        if self.phase != "collect":
            return
        self.condition_rows.append(self._make_row(message))
        if len(self.condition_rows) >= self.frames_per_condition:
            self.rows.extend(self.condition_rows)
            self.phase = "advance"

    def _start_next_condition(self) -> None:
        self.condition_index += 1
        if self.condition_index >= len(self.conditions):
            self._finish("")
            return
        range_m, bearing_deg = self.conditions[self.condition_index]
        try:
            camera, target = self._set_and_read_pose(range_m, bearing_deg)
        except (RuntimeError, ValueError, subprocess.SubprocessError) as exc:
            self._finish(str(exc))
            return
        self.actual_camera = camera
        self.actual_target = target
        self.condition_rows = []
        self.settle_remaining = self.settle_frames
        self.phase = "settle" if self.settle_frames > 0 else "collect"
        self.get_logger().info(
            f"Condition {self.condition_index + 1}/{len(self.conditions)}: "
            f"range={range_m:.1f} m, bearing={bearing_deg:.0f} deg"
        )

    def _set_and_read_pose(
        self,
        range_m: float,
        bearing_deg: float,
    ) -> tuple[EntityPose, EntityPose]:
        current = self._read_pose_message()
        camera = parse_entity_pose(current, "camera_rig")
        bearing = math.radians(bearing_deg)
        local_x = range_m * math.cos(bearing)
        local_y = range_m * math.sin(bearing)
        target_x = (
            camera.x
            + math.cos(camera.yaw) * local_x
            - math.sin(camera.yaw) * local_y
        )
        target_y = (
            camera.y
            + math.sin(camera.yaw) * local_x
            + math.cos(camera.yaw) * local_y
        )
        half_yaw = self.target_yaw / 2.0
        request = (
            'name: "visual_target" '
            f"position {{ x: {target_x:.10g} y: {target_y:.10g} "
            f"z: {self.target_z:.10g} }} "
            f"orientation {{ z: {math.sin(half_yaw):.10g} "
            f"w: {math.cos(half_yaw):.10g} }}"
        )
        command = [
            "gz",
            "service",
            "-s",
            self.pose_service,
            "--reqtype",
            "gz.msgs.Pose",
            "--reptype",
            "gz.msgs.Boolean",
            "--timeout",
            "2000",
            "--req",
            request,
        ]
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=5.0,
        )
        if "true" not in result.stdout.lower():
            raise RuntimeError("Gazebo rejected target pose request")
        actual = self._read_pose_message()
        return (
            parse_entity_pose(actual, "camera_rig"),
            parse_entity_pose(actual, "visual_target"),
        )

    def _read_pose_message(self) -> str:
        command = [
            "gz",
            "topic",
            "-e",
            "-t",
            self.pose_topic,
            "-n",
            "1",
        ]
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=5.0,
        )
        if not result.stdout.strip():
            raise RuntimeError("Gazebo pose topic returned no ground truth")
        return result.stdout

    def _ground_truth(self) -> tuple[float, float]:
        if self.actual_camera is None or self.actual_target is None:
            raise RuntimeError("Ground truth is unavailable")
        dx = self.actual_target.x - self.actual_camera.x
        dy = self.actual_target.y - self.actual_camera.y
        forward = math.cos(self.actual_camera.yaw) * dx
        forward += math.sin(self.actual_camera.yaw) * dy
        left = -math.sin(self.actual_camera.yaw) * dx
        left += math.cos(self.actual_camera.yaw) * dy
        return math.hypot(forward, left), math.atan2(left, forward)

    def _full_visibility(self) -> bool:
        if self.actual_camera is None or self.actual_target is None:
            return False
        focal_px = self.image_width / (
            2.0 * math.tan(self.horizontal_fov_rad / 2.0)
        )
        vertical_half_fov = math.atan(self.image_height / (2.0 * focal_px))
        half_x = self.target_size[0] / 2.0
        half_y = self.target_size[1] / 2.0
        half_z = self.target_size[2] / 2.0
        for offset_x in (-half_x, half_x):
            for offset_y in (-half_y, half_y):
                target_cos = math.cos(self.actual_target.yaw)
                target_sin = math.sin(self.actual_target.yaw)
                world_x = self.actual_target.x + target_cos * offset_x
                world_x -= target_sin * offset_y
                world_y = self.actual_target.y + target_sin * offset_x
                world_y += target_cos * offset_y
                if line_blocked(
                    self.actual_camera.x,
                    self.actual_camera.y,
                    world_x,
                    world_y,
                    self.obstacles,
                ):
                    return False
                dx = world_x - self.actual_camera.x
                dy = world_y - self.actual_camera.y
                forward = math.cos(self.actual_camera.yaw) * dx
                forward += math.sin(self.actual_camera.yaw) * dy
                left = -math.sin(self.actual_camera.yaw) * dx
                left += math.cos(self.actual_camera.yaw) * dy
                if forward <= 0.0:
                    return False
                if abs(math.atan2(left, forward)) > self.horizontal_fov_rad / 2.0:
                    return False
                for offset_z in (-half_z, half_z):
                    up = self.actual_target.z + offset_z
                    up -= self.actual_camera.z
                    if abs(math.atan2(up, forward)) > vertical_half_fov:
                        return False
        return True

    def _make_row(self, message: Vector3Stamped) -> dict[str, Any]:
        requested_range, requested_bearing = self.conditions[
            self.condition_index
        ]
        actual_range, actual_bearing = self._ground_truth()
        valid = (
            message.vector.z >= 0.5
            and math.isfinite(message.vector.x)
            and math.isfinite(message.vector.y)
        )
        measured_bearing_deg = math.degrees(message.vector.y) if valid else None
        actual_bearing_deg = math.degrees(actual_bearing)
        return {
            "scene": self.scene,
            "condition_id": self.condition_index,
            "requested_range_m": requested_range,
            "requested_bearing_deg": requested_bearing,
            "actual_range_m": actual_range,
            "actual_bearing_deg": actual_bearing_deg,
            "measured_range_m": message.vector.x if valid else None,
            "measured_bearing_deg": measured_bearing_deg,
            "valid": valid,
            "full_visibility": self._full_visibility(),
            "range_error_m": message.vector.x - actual_range if valid else None,
            "bearing_error_deg": (
                measured_bearing_deg - actual_bearing_deg if valid else None
            ),
            "stamp_sec": message.header.stamp.sec,
            "stamp_nanosec": message.header.stamp.nanosec,
        }

    def _finish(self, failure: str) -> None:
        if self.done:
            return
        self.failure = failure
        self.done = True
        self._write_results()
        self.exit_code = 0 if not failure else 1
        if failure:
            self.get_logger().error(failure)
        else:
            self.get_logger().info(f"Recorded {len(self.rows)} measurement rows")
        rclpy.shutdown()

    def _write_results(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        csv_path = self.output_dir / f"{self.scene}_samples.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(self.rows)
        summary = summarize_rows(self.rows)
        summary.update(
            {
                "scene": self.scene,
                "condition_count": len(self.conditions),
                "frames_per_condition": self.frames_per_condition,
                "failure": self.failure or None,
                "ground_truth_source": (
                    f"Gazebo {self.pose_topic}; evaluation process only"
                ),
            }
        )
        if self.failure:
            summary["status"] = "fail"
        summary_path = self.output_dir / f"{self.scene}_summary.json"
        summary_path.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = CameraGateEvaluator()
    try:
        rclpy.spin(node)
    finally:
        exit_code = node.exit_code
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    if exit_code:
        print("Camera gate evaluator failed; see scene summary.", file=sys.stderr)
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
