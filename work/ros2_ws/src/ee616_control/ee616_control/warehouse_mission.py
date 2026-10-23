"""Deterministic loading, transport, and unloading mission plan."""

from __future__ import annotations

from dataclasses import dataclass


ROBOT_NAMES = ("leader", "follower_1", "follower_2", "follower_3")
LOADED_POSITION = 1.52
HIDDEN_POSITION = 0.0


@dataclass(frozen=True)
class MissionSegment:
    """One bounded leader command and its presentation state."""

    state: str
    duration_s: float
    linear_mps: float = 0.0
    angular_rps: float = 0.0
    cargo_action: tuple[str, bool] | None = None


@dataclass(frozen=True)
class MissionOutput:
    """Command and cargo state at one mission time."""

    state: str
    linear_mps: float
    angular_rps: float
    cargo_loaded: dict[str, bool]
    complete: bool


def build_mission_segments(
    follower_count: int,
    *,
    startup_s: float = 10.0,
) -> tuple[MissionSegment, ...]:
    """Return the pair-first or three-follower warehouse mission."""
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

    # The loading queue ends in the central aisle. The verified gradual-turn
    # profile changes aisle without making multiple red targets overlap in a
    # follower camera, then finishes with a straight drop-off approach.
    segments.extend(
        [
            MissionSegment("WAREHOUSE_AISLE", 20.0, linear_mps=0.35),
            MissionSegment(
                "WAREHOUSE_TURN", 8.0, linear_mps=0.35, angular_rps=0.12
            ),
            MissionSegment("APPROACH_DROPOFF", 9.0, linear_mps=0.35),
            MissionSegment("DROPOFF_SETTLE", 2.5),
        ]
    )
    for robot in robots:
        segments.append(
            MissionSegment(
                f"UNLOAD_{robot.upper()}",
                1.5,
                cargo_action=(robot, False),
            )
        )
    return tuple(segments)


class WarehouseMissionPlan:
    """Resolve timed mission segments without depending on ROS."""

    def __init__(self, follower_count: int, *, startup_s: float = 10.0) -> None:
        self.follower_count = follower_count
        self.robots = ROBOT_NAMES[: follower_count + 1]
        self.segments = build_mission_segments(
            follower_count, startup_s=startup_s
        )
        self.total_duration_s = sum(segment.duration_s for segment in self.segments)

    def output(self, elapsed_s: float) -> MissionOutput:
        """Return the bounded command and latched cargo state at elapsed time."""
        elapsed_s = max(0.0, elapsed_s)
        cargo = {name: False for name in self.robots}
        remaining = elapsed_s
        for segment in self.segments:
            if segment.cargo_action is not None:
                robot, loaded = segment.cargo_action
                cargo[robot] = loaded
            if remaining < segment.duration_s:
                return MissionOutput(
                    state=segment.state,
                    linear_mps=segment.linear_mps,
                    angular_rps=segment.angular_rps,
                    cargo_loaded=cargo,
                    complete=False,
                )
            remaining -= segment.duration_s
        return MissionOutput(
            state="COMPLETE",
            linear_mps=0.0,
            angular_rps=0.0,
            cargo_loaded=cargo,
            complete=True,
        )


def cargo_position(loaded: bool) -> float:
    """Return the visual lift position for one cargo box."""
    return LOADED_POSITION if loaded else HIDDEN_POSITION
