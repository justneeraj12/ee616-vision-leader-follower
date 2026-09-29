"""Parse selected entities from Gazebo's text-format pose messages."""

from __future__ import annotations

import re
from dataclasses import dataclass
from math import atan2


@dataclass(frozen=True)
class EntityPose:
    """A world-frame entity pose."""

    x: float
    y: float
    z: float
    yaw: float


def _scalar(block: str, key: str, default: float) -> float:
    match = re.search(rf"^\s*{key}:\s*([-+0-9.eE]+)\s*$", block, re.MULTILINE)
    return float(match.group(1)) if match else default


def parse_entity_pose(message: str, entity_name: str) -> EntityPose:
    """Extract one named entity pose from a gz.msgs.Pose_V text message."""
    escaped = re.escape(entity_name)
    pattern = rf'^pose \{{\n  name: "{escaped}".*?(?=^pose \{{|\Z)'
    match = re.search(pattern, message, re.MULTILINE | re.DOTALL)
    if not match:
        raise ValueError(f"Entity {entity_name!r} was not present in pose message")
    entity = match.group(0)
    position = re.search(r"position \{(.*?)\n  \}", entity, re.DOTALL)
    orientation = re.search(r"orientation \{(.*?)\n  \}", entity, re.DOTALL)
    if not position or not orientation:
        raise ValueError(f"Entity {entity_name!r} pose was incomplete")

    x = _scalar(position.group(1), "x", 0.0)
    y = _scalar(position.group(1), "y", 0.0)
    z = _scalar(position.group(1), "z", 0.0)
    qx = _scalar(orientation.group(1), "x", 0.0)
    qy = _scalar(orientation.group(1), "y", 0.0)
    qz = _scalar(orientation.group(1), "z", 0.0)
    qw = _scalar(orientation.group(1), "w", 1.0)
    yaw = atan2(
        2.0 * (qw * qz + qx * qy),
        1.0 - 2.0 * (qy * qy + qz * qz),
    )
    return EntityPose(x=x, y=y, z=z, yaw=yaw)
