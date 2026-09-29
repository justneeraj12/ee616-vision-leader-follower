"""Evaluation-only geometric visibility checks."""

from __future__ import annotations

from math import cos, sin


def segment_intersects_box(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    obstacle: tuple[float, float, float, float, float],
) -> bool:
    """Return whether a 2-D segment enters an oriented obstacle box."""
    center_x, center_y, yaw, size_x, size_y = obstacle
    yaw_cos = cos(yaw)
    yaw_sin = sin(yaw)

    def local(world_x: float, world_y: float) -> tuple[float, float]:
        dx = world_x - center_x
        dy = world_y - center_y
        return yaw_cos * dx + yaw_sin * dy, -yaw_sin * dx + yaw_cos * dy

    local_start = local(start_x, start_y)
    local_end = local(end_x, end_y)
    direction = (
        local_end[0] - local_start[0],
        local_end[1] - local_start[1],
    )
    enter = 0.0
    leave = 1.0
    for origin, delta, half_size in (
        (local_start[0], direction[0], size_x / 2.0),
        (local_start[1], direction[1], size_y / 2.0),
    ):
        if abs(delta) < 1e-12:
            if abs(origin) > half_size:
                return False
            continue
        first = (-half_size - origin) / delta
        second = (half_size - origin) / delta
        if first > second:
            first, second = second, first
        enter = max(enter, first)
        leave = min(leave, second)
        if enter > leave:
            return False
    return leave >= 0.0 and enter < 1.0 - 1e-9


def line_blocked(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    obstacles: list[tuple[float, float, float, float, float]],
) -> bool:
    """Return whether any obstacle blocks a camera-to-target segment."""
    return any(
        segment_intersects_box(start_x, start_y, end_x, end_y, obstacle)
        for obstacle in obstacles
    )
