from math import isclose, radians, tan

import cv2
from ee616_perception.red_target import detect_red_target, focal_length_px
import numpy as np


def _synthetic_target(range_m: float, bearing_deg: float) -> np.ndarray:
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    fov = radians(70.0)
    focal = focal_length_px(640, fov)
    bearing = radians(bearing_deg)
    height = round(focal * 0.9 / (range_m * np.cos(bearing)))
    center_x = round(319.5 - focal * tan(bearing))
    cv2.rectangle(
        image,
        (center_x - 20, 240 - height // 2),
        (center_x + 20, 240 + height // 2 - 1),
        (230, 35, 15),
        -1,
    )
    return image


def test_detects_synthetic_range_and_positive_left_bearing():
    result = detect_red_target(
        _synthetic_target(3.0, 10.0),
        horizontal_fov_rad=radians(70.0),
        target_height_m=0.9,
    )
    assert result.valid
    assert isclose(result.range_m, 3.0, abs_tol=0.03)
    assert isclose(result.bearing_rad, radians(10.0), abs_tol=radians(0.2))


def test_returns_invalid_when_no_red_region_exists():
    result = detect_red_target(
        np.zeros((480, 640, 3), dtype=np.uint8),
        horizontal_fov_rad=radians(70.0),
        target_height_m=0.9,
    )
    assert not result.valid
    assert np.isnan(result.range_m)
    assert np.isnan(result.bearing_rad)


def test_rejects_invalid_image_shape():
    with np.testing.assert_raises(ValueError):
        detect_red_target(
            np.zeros((480, 640), dtype=np.uint8),
            horizontal_fov_rad=radians(70.0),
            target_height_m=0.9,
        )
