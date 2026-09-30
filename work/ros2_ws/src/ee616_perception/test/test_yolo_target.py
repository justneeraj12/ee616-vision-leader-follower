from math import isclose, radians, tan
from types import SimpleNamespace

from ee616_perception.yolo_target import (
    YoloTargetDetector,
    measurement_from_bbox,
)
import numpy as np


def test_bbox_geometry_recovers_range_and_positive_left_bearing():
    image_width = 640
    focal = image_width / (2.0 * tan(radians(70.0) / 2.0))
    bearing = radians(10.0)
    height = focal * 0.9 / (3.0 * np.cos(bearing))
    center = 319.5 - focal * tan(bearing)
    result = measurement_from_bbox(
        (center - 20.0, 240.0 - height / 2.0, center + 20.0, 240.0 + height / 2.0),
        image_width=image_width,
        horizontal_fov_rad=radians(70.0),
        target_height_m=0.9,
    )
    assert result.valid
    assert isclose(result.range_m, 3.0, abs_tol=0.001)
    assert isclose(result.bearing_rad, bearing, abs_tol=0.001)


class _FakeModel:
    def __init__(self, boxes):
        self.boxes = boxes
        self.last_source = None

    def predict(self, **kwargs):
        self.last_source = kwargs["source"]
        return [SimpleNamespace(boxes=self.boxes)]


def test_detector_selects_highest_confidence_target_class():
    boxes = SimpleNamespace(
        xyxy=np.array([[10.0, 10.0, 20.0, 20.0], [280.0, 160.0, 360.0, 320.0]]),
        cls=np.array([1.0, 0.0]),
        conf=np.array([0.99, 0.80]),
    )
    detector = YoloTargetDetector("unused.pt", model=_FakeModel(boxes))
    result = detector.detect(
        np.zeros((480, 640, 3), dtype=np.uint8),
        horizontal_fov_rad=radians(70.0),
        target_height_m=0.9,
    )
    assert result.valid
    assert result.bbox_x == 280
    assert result.bbox_height == 160
    assert detector.last_confidence == 0.80
    assert detector.last_bbox_xyxy == (280.0, 160.0, 360.0, 320.0)
    assert detector.last_inference_ms >= 0.0


def test_detector_returns_invalid_without_target_class():
    boxes = SimpleNamespace(
        xyxy=np.array([[10.0, 10.0, 20.0, 20.0]]),
        cls=np.array([2.0]),
        conf=np.array([0.99]),
    )
    detector = YoloTargetDetector("unused.pt", model=_FakeModel(boxes))
    result = detector.detect(
        np.zeros((480, 640, 3), dtype=np.uint8),
        horizontal_fov_rad=radians(70.0),
        target_height_m=0.9,
    )
    assert not result.valid
    assert detector.last_bbox_xyxy is None


def test_detector_converts_ros_rgb_array_to_ultralytics_bgr_array():
    boxes = SimpleNamespace(
        xyxy=np.empty((0, 4)),
        cls=np.empty(0),
        conf=np.empty(0),
    )
    model = _FakeModel(boxes)
    detector = YoloTargetDetector("unused.pt", model=model)
    rgb_image = np.array([[[240, 30, 10]]], dtype=np.uint8)
    detector.detect(
        rgb_image,
        horizontal_fov_rad=radians(70.0),
        target_height_m=0.9,
    )
    assert model.last_source.flags["C_CONTIGUOUS"]
    assert model.last_source[0, 0].tolist() == [10, 30, 240]


def test_validation_calibration_applies_to_raw_range():
    base = measurement_from_bbox(
        (280.0, 180.0, 360.0, 300.0),
        image_width=640,
        horizontal_fov_rad=radians(70.0),
        target_height_m=0.9,
    )
    calibrated = measurement_from_bbox(
        (280.0, 180.0, 360.0, 300.0),
        image_width=640,
        horizontal_fov_rad=radians(70.0),
        target_height_m=0.9,
        range_scale=1.1,
        range_offset_m=-0.2,
    )
    assert isclose(calibrated.range_m, 1.1 * base.range_m - 0.2)
