from math import isclose, pi

from ee616_evaluation.pose_text import parse_entity_pose

import pytest


POSE_MESSAGE = """pose {
  name: "camera_rig"
  id: 8
  position {
    x: -6
    z: 0.65
  }
  orientation {
    w: 1
  }
}
pose {
  name: "visual_target"
  id: 11
  position {
    x: -3
    y: 1
    z: 0.6
  }
  orientation {
    z: 0.7071067812
    w: 0.7071067812
  }
}
"""


def test_parses_position_defaults_and_yaw():
    camera = parse_entity_pose(POSE_MESSAGE, "camera_rig")
    target = parse_entity_pose(POSE_MESSAGE, "visual_target")
    assert camera.x == -6.0
    assert camera.y == 0.0
    assert camera.z == 0.65
    assert target.y == 1.0
    assert isclose(target.yaw, pi / 2.0, abs_tol=1e-9)


def test_missing_entity_is_rejected():
    with pytest.raises(ValueError, match="not present"):
        parse_entity_pose(POSE_MESSAGE, "missing")
