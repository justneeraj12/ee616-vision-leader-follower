"""Pure convoy-governor decisions for the mapped warehouse mission."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FollowerHealth:
    """Supervisor and estimator health reported by one follower."""

    state: str
    bearing_rad: float | None
    measurement_age_s: float | None
    telemetry_age_s: float | None


@dataclass(frozen=True)
class GovernorDecision:
    """One bounded leader-command decision."""

    mode: str
    reason: str
    linear_scale: float
    hold: bool


def navigation_active(mission_state: str) -> bool:
    """Return whether Nav2 is planning or following a mission leg."""
    return mission_state.startswith(("PLAN_", "NAV_", "RECOVER_"))


def decide_governor(
    followers: list[FollowerHealth],
    *,
    mission_state: str,
    fault_active: bool = False,
    bearing_caution_rad: float = 0.35,
    measurement_age_caution_s: float = 0.20,
    telemetry_timeout_s: float = 0.75,
    caution_scale: float = 0.55,
) -> GovernorDecision:
    """Choose normal, caution, or hold without using simulator truth."""
    if not navigation_active(mission_state):
        return GovernorDecision("MISSION", "pre/post navigation command", 1.0, False)
    if fault_active:
        return GovernorDecision("FAULT_HOLD", "injected leader command dropout", 0.0, True)
    if not followers:
        return GovernorDecision("HOLD", "no follower health configured", 0.0, True)
    for index, follower in enumerate(followers, start=1):
        if (
            follower.telemetry_age_s is None
            or follower.telemetry_age_s > telemetry_timeout_s
        ):
            return GovernorDecision(
                "HOLD", f"follower_{index} supervisor telemetry stale", 0.0, True
            )
        if follower.state in {"SAFE_STOP", "OFFLINE", "UNSEEN"}:
            return GovernorDecision(
                "HOLD", f"follower_{index} reported {follower.state}", 0.0, True
            )
    for index, follower in enumerate(followers, start=1):
        if follower.state == "PREDICT":
            return GovernorDecision(
                "CAUTION", f"follower_{index} reported PREDICT", caution_scale, False
            )
        if (
            follower.measurement_age_s is not None
            and follower.measurement_age_s >= measurement_age_caution_s
        ):
            return GovernorDecision(
                "CAUTION",
                f"follower_{index} measurement age is elevated",
                caution_scale,
                False,
            )
        if (
            follower.bearing_rad is not None
            and abs(follower.bearing_rad) >= bearing_caution_rad
        ):
            return GovernorDecision(
                "CAUTION",
                f"follower_{index} predecessor bearing is large",
                caution_scale,
                False,
            )
    return GovernorDecision("NORMAL", "all followers report TRACK", 1.0, False)
