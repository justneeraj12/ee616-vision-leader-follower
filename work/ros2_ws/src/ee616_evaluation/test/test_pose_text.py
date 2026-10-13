from math import isclose, pi

import os
import subprocess

from ee616_evaluation.pose_text import parse_entity_pose, read_gz_topic_text

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


def test_gz_topic_reader_removes_gui_only_prime_environment(monkeypatch):
    monkeypatch.setenv("__GLX_VENDOR_LIBRARY_NAME", "nvidia")
    monkeypatch.setenv("__NV_PRIME_RENDER_OFFLOAD", "1")
    captured = {}

    def run(*args, **kwargs):
        captured.update(kwargs)
        return subprocess.CompletedProcess(args[0], 0, stdout="pose {}")

    monkeypatch.setattr(subprocess, "run", run)
    assert read_gz_topic_text("/world/test/pose/info") == "pose {}"
    assert "__GLX_VENDOR_LIBRARY_NAME" not in captured["env"]
    assert "__NV_PRIME_RENDER_OFFLOAD" not in captured["env"]
    assert os.environ["__GLX_VENDOR_LIBRARY_NAME"] == "nvidia"
