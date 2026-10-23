"""Pure mission definitions for the mapped Nav2 warehouse demonstration."""

from __future__ import annotations

from dataclasses import dataclass
import math

from ee616_control.warehouse_mission import MissionSegment, ROBOT_NAMES


@dataclass(frozen=True)
class NavWaypoint:
    """One map-frame goal for the route-owning leader."""

    name: str
    x_m: float
    y_m: float
    yaw_rad: float


NAV_WAYPOINTS = (
    NavWaypoint("BOTTOM_AISLE_EAST", 7.0, -6.0, 0.0),
    NavWaypoint("TURN_ENTRY", 10.5, -2.5, math.pi / 2.0),
    NavWaypoint("RIGHT_CROSS_AISLE", 7.0, -1.0, math.pi),
    NavWaypoint("DISPATCH_DOCK", -10.0, -1.0, math.pi),
)


def build_loading_segments(
    follower_count: int,
    *,
    startup_s: float = 10.0,
) -> tuple[MissionSegment, ...]:
    """Return deterministic station loading before Nav2 takes command."""
    if follower_count not in {1, 3}:
        raise ValueError("follower_count must be 1 or 3")
    if not 0.0 <= startup_s <= 30.0:
        raise ValueError("startup_s must be between 0 and 30")
    robots = ROBOT_NAMES[: follower_count + 1]
    segments: list[MissionSegment] = [MissionSegment("SETTLE", startup_s)]
    for index, robot in enumerate(robots):
        if index:
            segments.append(
                MissionSegment(
                    f"ADVANCE_TO_{robot.upper()}",
                    5.8,
                    linear_mps=0.35,
                )
            )
        segments.append(
            MissionSegment(
                f"LOAD_{robot.upper()}",
                3.0,
                cargo_action=(robot, True),
            )
        )
    segments.append(MissionSegment("NAV2_HANDOFF", 2.0))
    return tuple(segments)


def loading_duration_s(follower_count: int, startup_s: float = 10.0) -> float:
    return sum(
        segment.duration_s
        for segment in build_loading_segments(
            follower_count,
            startup_s=startup_s,
        )
    )
