import math

import pytest

from ee616_control.warehouse_nav_mission import (
    NAV_WAYPOINTS,
    build_loading_segments,
    loading_duration_s,
)


def test_nav_route_has_multiple_aisles_and_turns():
    assert len(NAV_WAYPOINTS) == 4
    assert {waypoint.y_m for waypoint in NAV_WAYPOINTS} == {-6.0, -2.5, -1.0}
    assert len({waypoint.yaw_rad for waypoint in NAV_WAYPOINTS}) >= 3
    assert NAV_WAYPOINTS[-1].name == "DISPATCH_DOCK"
    assert NAV_WAYPOINTS[-1].yaw_rad == pytest.approx(math.pi)


@pytest.mark.parametrize("follower_count", [1, 3])
def test_loading_is_pair_first_compatible_and_bounded(follower_count):
    segments = build_loading_segments(follower_count, startup_s=4.0)
    loads = [
        segment.cargo_action[0]
        for segment in segments
        if segment.cargo_action is not None
    ]
    expected = ["leader"] + [
        f"follower_{index}" for index in range(1, follower_count + 1)
    ]
    assert loads == expected
    assert all(0.0 <= segment.linear_mps <= 0.35 for segment in segments)
    assert loading_duration_s(follower_count, 4.0) == pytest.approx(
        sum(segment.duration_s for segment in segments)
    )


def test_loading_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        build_loading_segments(2)
    with pytest.raises(ValueError):
        build_loading_segments(1, startup_s=-1.0)
