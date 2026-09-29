"""Deterministic red-target camera geometry baseline."""

from __future__ import annotations

from dataclasses import dataclass
from math import atan, cos, isfinite, tan

import cv2
import numpy as np


@dataclass(frozen=True)
class CameraMeasurement:
    """One relative measurement and its image-space evidence."""

    valid: bool
    range_m: float
    bearing_rad: float
    bbox_x: int = 0
    bbox_y: int = 0
    bbox_width: int = 0
    bbox_height: int = 0
    area_px: float = 0.0


def focal_length_px(image_width: int, horizontal_fov_rad: float) -> float:
    """Return horizontal focal length from image width and field of view."""
    if image_width <= 0:
        raise ValueError("image_width must be positive")
    if not 0.0 < horizontal_fov_rad < 3.141592653589793:
        raise ValueError("horizontal_fov_rad must be between zero and pi")
    return image_width / (2.0 * tan(horizontal_fov_rad / 2.0))


def detect_red_target(
    rgb_image: np.ndarray,
    *,
    horizontal_fov_rad: float,
    target_height_m: float,
    min_saturation: int = 80,
    min_value: int = 50,
    min_area_px: float = 80.0,
    min_height_px: int = 5,
) -> CameraMeasurement:
    """Detect the largest red region and estimate planar range and bearing.

    The estimate uses only image pixels and fixed calibration parameters. The
    bearing convention is positive left, matching a ROS base frame.
    """
    if rgb_image.ndim != 3 or rgb_image.shape[2] != 3:
        raise ValueError("rgb_image must have shape (height, width, 3)")
    if target_height_m <= 0.0:
        raise ValueError("target_height_m must be positive")

    hsv = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2HSV)
    low_red = cv2.inRange(
        hsv,
        np.array([0, min_saturation, min_value], dtype=np.uint8),
        np.array([12, 255, 255], dtype=np.uint8),
    )
    high_red = cv2.inRange(
        hsv,
        np.array([168, min_saturation, min_value], dtype=np.uint8),
        np.array([179, 255, 255], dtype=np.uint8),
    )
    mask = cv2.bitwise_or(low_red, high_red)
    kernel = np.ones((3, 3), dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    if not contours:
        return CameraMeasurement(False, float("nan"), float("nan"))

    contour = max(contours, key=cv2.contourArea)
    area = float(cv2.contourArea(contour))
    x, y, width, height = cv2.boundingRect(contour)
    if area < min_area_px or height < min_height_px:
        return CameraMeasurement(
            False,
            float("nan"),
            float("nan"),
            x,
            y,
            width,
            height,
            area,
        )

    image_width = int(rgb_image.shape[1])
    focal_px = focal_length_px(image_width, horizontal_fov_rad)
    center_u = x + (width - 1) / 2.0
    principal_u = (image_width - 1) / 2.0
    bearing_rad = atan((principal_u - center_u) / focal_px)
    forward_depth_m = focal_px * target_height_m / float(height)
    range_m = forward_depth_m / cos(bearing_rad)
    valid = isfinite(range_m) and isfinite(bearing_rad) and range_m > 0.0
    return CameraMeasurement(
        valid,
        range_m if valid else float("nan"),
        bearing_rad if valid else float("nan"),
        x,
        y,
        width,
        height,
        area,
    )
