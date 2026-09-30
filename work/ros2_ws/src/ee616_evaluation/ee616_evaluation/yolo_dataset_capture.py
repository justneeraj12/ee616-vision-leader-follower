"""Capture deterministic Gazebo images and evaluation-only YOLO labels."""

from __future__ import annotations

import json
import math
import subprocess
import time
from pathlib import Path
from typing import Any

import cv2
from cv_bridge import CvBridge
from ee616_evaluation.dataset_labels import project_target_box
from ee616_evaluation.pose_text import EntityPose, parse_entity_pose
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


class YoloDatasetCapture(Node):
    """Move a known target and save images plus offline YOLO annotations."""

    def __init__(self) -> None:
        super().__init__("yolo_dataset_capture")
        self.declare_parameter("scene", "yolo_train_open")
        self.declare_parameter("split", "train")
        self.declare_parameter("image_topic", "/smoke/camera/image")
        self.declare_parameter(
            "output_dir",
            "/workspace/work/ros2_ws/datasets/ee616_predecessor_target_v1",
        )
        self.declare_parameter("frames_per_condition", 3)
        self.declare_parameter("settle_frames", 3)
        self.declare_parameter("start_condition_index", 0)
        self.declare_parameter("timeout_s", 240.0)
        self.declare_parameter("ranges_m", [1.2, 1.8, 2.4, 3.2, 4.2, 5.2])
        self.declare_parameter(
            "bearings_deg",
            [-48.0, -28.0, -18.0, -8.0, 0.0, 8.0, 18.0, 28.0, 48.0],
        )
        self.declare_parameter("horizontal_fov_rad", 1.2217304764)
        self.declare_parameter("image_width", 640)
        self.declare_parameter("image_height", 480)
        self.declare_parameter("target_size", [0.08, 0.7, 0.9])
        self.declare_parameter("target_z", 0.6)
        self.declare_parameter("target_yaw", 0.0)
        self.declare_parameter("class_id", 0)
        self.declare_parameter("class_name", "predecessor_target")

        self.scene = str(self.get_parameter("scene").value)
        self.split = str(self.get_parameter("split").value)
        if self.split not in {"train", "val", "test"}:
            raise ValueError("split must be train, val, or test")
        self.output_dir = Path(str(self.get_parameter("output_dir").value))
        self.frames_per_condition = int(
            self.get_parameter("frames_per_condition").value
        )
        self.settle_frames = int(self.get_parameter("settle_frames").value)
        self.start_condition_index = int(
            self.get_parameter("start_condition_index").value
        )
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
        if not 0 <= self.start_condition_index < len(self.conditions):
            raise ValueError(
                "start_condition_index must select an available condition"
            )
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
        self.class_id = int(self.get_parameter("class_id").value)
        self.class_name = str(self.get_parameter("class_name").value)

        self.images_dir = self.output_dir / "images" / self.split
        self.labels_dir = self.output_dir / "labels" / self.split
        self.metadata_dir = self.output_dir / "metadata"
        for directory in (self.images_dir, self.labels_dir, self.metadata_dir):
            directory.mkdir(parents=True, exist_ok=True)

        image_topic = str(self.get_parameter("image_topic").value)
        self.bridge = CvBridge()
        self.subscription = self.create_subscription(
            Image,
            image_topic,
            self._receive_image,
            qos_profile_sensor_data,
        )
        self.timer = self.create_timer(0.1, self._tick)
        self.started = time.monotonic()
        self.phase = "waiting"
        self.received_any = False
        self.condition_index = self.start_condition_index - 1
        self.condition_frames = 0
        self.settle_remaining = 0
        self.camera_pose: EntityPose | None = None
        self.target_pose: EntityPose | None = None
        self.records = self._load_prior_records()
        self.done = False
        self.exit_code = 1

    def _load_prior_records(self) -> list[dict[str, Any]]:
        """Retain completed metadata when resuming an interrupted capture."""
        if self.start_condition_index == 0:
            return []
        summary_path = self.metadata_dir / f"{self.split}_{self.scene}.json"
        if not summary_path.is_file():
            raise ValueError(
                "resume requested but prior capture metadata is unavailable"
            )
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if (
            summary.get("scene") != self.scene
            or summary.get("split") != self.split
        ):
            raise ValueError("prior capture metadata does not match this run")
        records = [
            record
            for record in summary.get("records", [])
            if int(record["condition_id"]) < self.start_condition_index
        ]
        expected = self.start_condition_index * self.frames_per_condition
        if len(records) != expected:
            raise ValueError(
                f"resume expected {expected} prior records, found {len(records)}"
            )
        return records

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
            self._finish(f"dataset capture timed out during {self.phase}")
            return
        if self.phase == "waiting" and self.received_any:
            self._start_next_condition()
        elif self.phase == "advance":
            self._start_next_condition()

    def _receive_image(self, message: Image) -> None:
        self.received_any = True
        if self.phase == "settle":
            self.settle_remaining -= 1
            if self.settle_remaining <= 0:
                self.phase = "collect"
            return
        if self.phase != "collect":
            return
        try:
            rgb_image = self.bridge.imgmsg_to_cv2(
                message,
                desired_encoding="rgb8",
            )
            self._save_sample(rgb_image, message)
        except (ValueError, TypeError, OSError) as exc:
            self._finish(f"unable to save dataset sample: {exc}")
            return
        self.condition_frames += 1
        if self.condition_frames >= self.frames_per_condition:
            self.phase = "advance"

    def _start_next_condition(self) -> None:
        self.condition_index += 1
        if self.condition_index >= len(self.conditions):
            self._finish("")
            return
        range_m, bearing_deg = self.conditions[self.condition_index]
        try:
            self.camera_pose, self.target_pose = self._set_and_read_pose(
                range_m,
                bearing_deg,
            )
        except (RuntimeError, ValueError, subprocess.SubprocessError) as exc:
            self._finish(str(exc))
            return
        self.condition_frames = 0
        self.settle_remaining = self.settle_frames
        self.phase = "settle" if self.settle_frames > 0 else "collect"
        self.get_logger().info(
            f"{self.split} {self.scene} condition "
            f"{self.condition_index + 1}/{len(self.conditions)}: "
            f"range={range_m:.1f} bearing={bearing_deg:.0f}"
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
        target_x = camera.x + math.cos(camera.yaw) * local_x
        target_x -= math.sin(camera.yaw) * local_y
        target_y = camera.y + math.sin(camera.yaw) * local_x
        target_y += math.cos(camera.yaw) * local_y
        half_yaw = self.target_yaw / 2.0
        request = (
            'name: "visual_target" '
            f"position {{ x: {target_x:.10g} y: {target_y:.10g} "
            f"z: {self.target_z:.10g} }} "
            f"orientation {{ z: {math.sin(half_yaw):.10g} "
            f"w: {math.cos(half_yaw):.10g} }}"
        )
        result = subprocess.run(
            [
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
            ],
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
        result = subprocess.run(
            ["gz", "topic", "-e", "-t", self.pose_topic, "-n", "1"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5.0,
        )
        if not result.stdout.strip():
            raise RuntimeError("Gazebo pose topic returned no ground truth")
        return result.stdout

    def _save_sample(self, rgb_image, message: Image) -> None:
        if self.camera_pose is None or self.target_pose is None:
            raise RuntimeError("target pose is unavailable")
        stem = (
            f"{self.scene}_c{self.condition_index:03d}_"
            f"f{self.condition_frames:02d}"
        )
        image_path = self.images_dir / f"{stem}.png"
        label_path = self.labels_dir / f"{stem}.txt"
        bgr_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
        if not cv2.imwrite(str(image_path), bgr_image):
            raise OSError(f"OpenCV did not write {image_path}")
        box = project_target_box(
            self.camera_pose,
            self.target_pose,
            self.target_size,
            image_width=self.image_width,
            image_height=self.image_height,
            horizontal_fov_rad=self.horizontal_fov_rad,
        )
        label_path.write_text(
            box.label_line(self.class_id) if box is not None else "",
            encoding="utf-8",
        )
        requested_range, requested_bearing = self.conditions[self.condition_index]
        self.records.append(
            {
                "bearing_deg": requested_bearing,
                "class_name": self.class_name,
                "condition_id": self.condition_index,
                "frame": self.condition_frames,
                "image": str(image_path.relative_to(self.output_dir)),
                "label": str(label_path.relative_to(self.output_dir)),
                "positive_label": box is not None,
                "range_m": requested_range,
                "stamp_nanosec": message.header.stamp.nanosec,
                "stamp_sec": message.header.stamp.sec,
            }
        )

    def _finish(self, failure: str) -> None:
        if self.done:
            return
        self.done = True
        summary = {
            "annotation_source": "evaluation-only Gazebo pose projection",
            "class_id": self.class_id,
            "class_name": self.class_name,
            "failure": failure or None,
            "images": len(self.records),
            "negative_labels": sum(
                not record["positive_label"] for record in self.records
            ),
            "positive_labels": sum(
                record["positive_label"] for record in self.records
            ),
            "records": self.records,
            "scene": self.scene,
            "scope": "offline dataset evidence only; never a perception input",
            "split": self.split,
            "status": "fail" if failure else "pass",
            "target_size_m": self.target_size,
        }
        summary_path = self.metadata_dir / f"{self.split}_{self.scene}.json"
        summary_path.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.exit_code = 1 if failure else 0
        if failure:
            self.get_logger().error(failure)
        else:
            self.get_logger().info(
                f"Saved {len(self.records)} images for {self.scene}"
            )
        rclpy.shutdown()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = YoloDatasetCapture()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node._finish("capture interrupted")
    finally:
        exit_code = node.exit_code
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
