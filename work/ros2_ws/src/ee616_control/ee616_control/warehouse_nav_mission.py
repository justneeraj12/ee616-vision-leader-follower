"""Pure mission definitions for the mapped Nav2 warehouse demonstration."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ee616_control.warehouse_mission import MissionSegment, ROBOT_NAMES


@dataclass(frozen=True)
class NavWaypoint:
    """One map-frame goal for the route-owning leader."""

    name: str
    x_m: float
    y_m: float
    yaw_rad: float


STANDARD_WAYPOINTS = (
    NavWaypoint("BOTTOM_AISLE_EAST", 7.0, -6.0, 0.0),
    NavWaypoint("TURN_ENTRY", 10.5, -2.5, math.pi / 2.0),
    NavWaypoint("RIGHT_CROSS_AISLE", 7.0, -1.0, math.pi),
    NavWaypoint("DISPATCH_DOCK", -10.0, -1.0, math.pi),
)

WIDE_WAYPOINTS = (
    NavWaypoint("BOTTOM_AISLE_EAST", 10.0, -6.0, 0.0),
    NavWaypoint("RIGHT_CROSS_AISLE", 10.0, -1.0, math.pi / 2.0),
    NavWaypoint("DISPATCH_DOCK", -10.0, -1.0, math.pi),
)

TURN_DENSE_WAYPOINTS = (
    NavWaypoint("BOTTOM_AISLE_EAST", 10.0, -6.0, 0.0),
    NavWaypoint("RIGHT_CROSS_AISLE_1", 10.0, -1.0, math.pi / 2.0),
    NavWaypoint("MIDDLE_AISLE_WEST", -10.0, -1.0, math.pi),
    NavWaypoint("LEFT_CROSS_AISLE_1", -10.0, 4.75, math.pi / 2.0),
    NavWaypoint("UPPER_AISLE_EAST", 10.0, 4.75, 0.0),
    NavWaypoint("RIGHT_CROSS_AISLE_2", 10.0, 10.0, math.pi / 2.0),
    NavWaypoint("TOP_AISLE_WEST", -10.0, 10.0, math.pi),
    NavWaypoint("DISPATCH_DOCK", -10.0, -1.0, -math.pi / 2.0),
)

ROUTE_PROFILES = {
    "wide": WIDE_WAYPOINTS,
    "standard": STANDARD_WAYPOINTS,
    "turn_dense": TURN_DENSE_WAYPOINTS,
}

# Preserve the original public name for the frozen standard mission and older
# documentation. New configurable runs use route_waypoints().
NAV_WAYPOINTS = STANDARD_WAYPOINTS


def route_waypoints(profile: str) -> tuple[NavWaypoint, ...]:
    """Return one validated, deterministic route profile."""
    try:
        return ROUTE_PROFILES[profile]
    except KeyError as error:
        choices = ", ".join(sorted(ROUTE_PROFILES))
        raise ValueError(f"route_profile must be one of: {choices}") from error


def build_loading_segments(
    follower_count: int,
    *,
    startup_s: float = 10.0,
) -> tuple[MissionSegment, ...]:
    """Return deterministic station loading before Nav2 takes command."""
    if follower_count not in {1, 2, 3}:
        raise ValueError("follower_count must be 1, 2, or 3")
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
