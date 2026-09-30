"""Evaluation-only projection helpers for YOLO dataset labels."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, sin, tan

from ee616_evaluation.pose_text import EntityPose


@dataclass(frozen=True)
class YoloBox:
    """One normalized YOLO-format bounding box."""

    center_x: float
    center_y: float
    width: float
    height: float

    def label_line(self, class_id: int) -> str:
        """Return one Ultralytics label line."""
        return (
            f"{class_id} {self.center_x:.8f} {self.center_y:.8f} "
            f"{self.width:.8f} {self.height:.8f}\n"
        )


def project_target_box(
    camera: EntityPose,
    target: EntityPose,
    target_size: tuple[float, float, float],
    *,
    image_width: int,
    image_height: int,
    horizontal_fov_rad: float,
) -> YoloBox | None:
    """Project a known 3-D target box into a clipped image-space box.

    This helper belongs to the evaluation package. Its Gazebo pose inputs must
    never be passed to perception or control.
    """
    if image_width <= 0 or image_height <= 0:
        raise ValueError("image dimensions must be positive")
    if not 0.0 < horizontal_fov_rad < 3.141592653589793:
        raise ValueError("horizontal_fov_rad must be between zero and pi")
    if len(target_size) != 3 or any(value <= 0.0 for value in target_size):
        raise ValueError("target_size must contain three positive values")

    focal_px = image_width / (2.0 * tan(horizontal_fov_rad / 2.0))
    principal_x = (image_width - 1) / 2.0
    principal_y = (image_height - 1) / 2.0
    half_x, half_y, half_z = (value / 2.0 for value in target_size)
    projected: list[tuple[float, float]] = []

    for local_x in (-half_x, half_x):
        for local_y in (-half_y, half_y):
            world_x = target.x + cos(target.yaw) * local_x
            world_x -= sin(target.yaw) * local_y
            world_y = target.y + sin(target.yaw) * local_x
            world_y += cos(target.yaw) * local_y
            dx = world_x - camera.x
            dy = world_y - camera.y
            forward = cos(camera.yaw) * dx + sin(camera.yaw) * dy
            left = -sin(camera.yaw) * dx + cos(camera.yaw) * dy
            if forward <= 0.0:
                continue
            for local_z in (-half_z, half_z):
                up = target.z + local_z - camera.z
                pixel_x = principal_x - focal_px * left / forward
                pixel_y = principal_y - focal_px * up / forward
                projected.append((pixel_x, pixel_y))

    if not projected:
        return None
    raw_left = min(point[0] for point in projected)
    raw_right = max(point[0] for point in projected)
    raw_top = min(point[1] for point in projected)
    raw_bottom = max(point[1] for point in projected)
    if (
        raw_right < 0.0
        or raw_left > image_width - 1
        or raw_bottom < 0.0
        or raw_top > image_height - 1
    ):
        return None

    left_px = max(0.0, raw_left)
    right_px = min(float(image_width - 1), raw_right)
    top_px = max(0.0, raw_top)
    bottom_px = min(float(image_height - 1), raw_bottom)
    width_px = right_px - left_px
    height_px = bottom_px - top_px
    if width_px < 1.0 or height_px < 1.0:
        return None
    return YoloBox(
        center_x=((left_px + right_px) / 2.0) / image_width,
        center_y=((top_px + bottom_px) / 2.0) / image_height,
        width=width_px / image_width,
        height=height_px / image_height,
    )
