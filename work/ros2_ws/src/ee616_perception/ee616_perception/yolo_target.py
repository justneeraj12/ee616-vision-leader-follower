"""YOLO target detection with camera-only range and bearing geometry."""

from __future__ import annotations

from math import atan, cos, isfinite
from pathlib import Path
from time import perf_counter
from typing import Any

from ee616_perception.red_target import CameraMeasurement, focal_length_px
import numpy as np


def measurement_from_bbox(
    bbox_xyxy: tuple[float, float, float, float],
    *,
    image_width: int,
    horizontal_fov_rad: float,
    target_height_m: float,
    range_scale: float = 1.0,
    range_offset_m: float = 0.0,
) -> CameraMeasurement:
    """Convert one detected bounding box into planar range and bearing."""
    x_min, y_min, x_max, y_max = bbox_xyxy
    width = x_max - x_min
    height = y_max - y_min
    if target_height_m <= 0.0:
        raise ValueError("target_height_m must be positive")
    if range_scale <= 0.0:
        raise ValueError("range_scale must be positive")
    if width <= 0.0 or height <= 0.0:
        return CameraMeasurement(False, float("nan"), float("nan"))
    focal_px = focal_length_px(image_width, horizontal_fov_rad)
    center_u = (x_min + x_max) / 2.0
    principal_u = (image_width - 1) / 2.0
    bearing_rad = atan((principal_u - center_u) / focal_px)
    forward_depth_m = focal_px * target_height_m / height
    raw_range_m = forward_depth_m / cos(bearing_rad)
    range_m = range_scale * raw_range_m + range_offset_m
    valid = isfinite(range_m) and isfinite(bearing_rad) and range_m > 0.0
    return CameraMeasurement(
        valid=valid,
        range_m=range_m if valid else float("nan"),
        bearing_rad=bearing_rad if valid else float("nan"),
        bbox_x=int(round(x_min)),
        bbox_y=int(round(y_min)),
        bbox_width=int(round(width)),
        bbox_height=int(round(height)),
        area_px=float(width * height),
    )


def _numpy(value: Any) -> np.ndarray:
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        value = value.numpy()
    return np.asarray(value)


class YoloTargetDetector:
    """Run an Ultralytics model and select the best target-class box."""

    def __init__(
        self,
        weights_path: str,
        *,
        class_id: int = 0,
        confidence: float = 0.25,
        iou: float = 0.45,
        image_size: int = 640,
        device: str = "0",
        range_scale: float = 1.0,
        range_offset_m: float = 0.0,
        model: Any | None = None,
    ) -> None:
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between zero and one")
        if not 0.0 <= iou <= 1.0:
            raise ValueError("iou must be between zero and one")
        if image_size <= 0:
            raise ValueError("image_size must be positive")
        if range_scale <= 0.0:
            raise ValueError("range_scale must be positive")
        if model is None:
            path = Path(weights_path)
            if not path.is_file():
                raise FileNotFoundError(f"YOLO weights do not exist: {path}")
            from ultralytics import YOLO

            model = YOLO(str(path))
        self.model = model
        self.class_id = class_id
        self.confidence = confidence
        self.iou = iou
        self.image_size = image_size
        self.device = device
        self.range_scale = range_scale
        self.range_offset_m = range_offset_m
        self.last_inference_ms = float("nan")
        self.last_confidence = float("nan")
        self.last_bbox_xyxy: tuple[float, float, float, float] | None = None

    def detect(
        self,
        rgb_image: np.ndarray,
        *,
        horizontal_fov_rad: float,
        target_height_m: float,
    ) -> CameraMeasurement:
        """Return the highest-confidence target measurement from one image."""
        if rgb_image.ndim != 3 or rgb_image.shape[2] != 3:
            raise ValueError("rgb_image must have shape (height, width, 3)")
        bgr_image = np.ascontiguousarray(rgb_image[..., ::-1])
        started = perf_counter()
        self.last_confidence = float("nan")
        self.last_bbox_xyxy = None
        results = self.model.predict(
            source=bgr_image,
            imgsz=self.image_size,
            conf=self.confidence,
            iou=self.iou,
            classes=[self.class_id],
            device=self.device,
            verbose=False,
        )
        self.last_inference_ms = (perf_counter() - started) * 1000.0
        if not results or results[0].boxes is None:
            return CameraMeasurement(False, float("nan"), float("nan"))
        boxes = results[0].boxes
        coordinates = _numpy(boxes.xyxy)
        classes = _numpy(boxes.cls).astype(int)
        confidences = _numpy(boxes.conf)
        candidates = np.flatnonzero(classes == self.class_id)
        if candidates.size == 0:
            return CameraMeasurement(False, float("nan"), float("nan"))
        best_index = int(candidates[np.argmax(confidences[candidates])])
        bbox = tuple(float(value) for value in coordinates[best_index])
        self.last_confidence = float(confidences[best_index])
        self.last_bbox_xyxy = bbox
        return measurement_from_bbox(
            bbox,
            image_width=int(rgb_image.shape[1]),
            horizontal_fov_rad=horizontal_fov_rad,
            target_height_m=target_height_m,
            range_scale=self.range_scale,
            range_offset_m=self.range_offset_m,
        )
