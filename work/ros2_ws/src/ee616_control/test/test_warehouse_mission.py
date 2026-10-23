"""Tests for the deterministic warehouse cargo mission."""

import pytest

from ee616_control.warehouse_mission import (
    HIDDEN_POSITION,
    LOADED_POSITION,
    WarehouseMissionPlan,
    build_mission_segments,
    cargo_position,
)


def test_pair_loads_in_order_and_finishes_empty():
    plan = WarehouseMissionPlan(1, startup_s=1.0)
    states = [segment.state for segment in plan.segments]
    assert states[:4] == [
        "SETTLE",
        "LOAD_LEADER",
        "ADVANCE_TO_FOLLOWER_1",
        "LOAD_FOLLOWER_1",
    ]
    assert plan.output(plan.total_duration_s + 0.1).complete
    assert not any(plan.output(plan.total_duration_s + 0.1).cargo_loaded.values())


def test_three_follower_load_and_unload_order():
    plan = WarehouseMissionPlan(3, startup_s=2.0)
    load_states = [
        segment.state for segment in plan.segments if segment.state.startswith("LOAD_")
    ]
    unload_states = [
        segment.state for segment in plan.segments if segment.state.startswith("UNLOAD_")
    ]
    assert load_states == [
        "LOAD_LEADER",
        "LOAD_FOLLOWER_1",
        "LOAD_FOLLOWER_2",
        "LOAD_FOLLOWER_3",
    ]
    assert unload_states == [state.replace("LOAD_", "UNLOAD_") for state in load_states]


def test_cargo_latches_after_loading_segment_begins():
    plan = WarehouseMissionPlan(3, startup_s=1.0)
    leader_loading = plan.output(1.1)
    assert leader_loading.state == "LOAD_LEADER"
    assert leader_loading.cargo_loaded["leader"]
    assert not leader_loading.cargo_loaded["follower_1"]


def test_cargo_positions_are_bounded():
    assert cargo_position(False) == HIDDEN_POSITION
    assert cargo_position(True) == LOADED_POSITION


@pytest.mark.parametrize("count", [0, 2, 4])
def test_unsupported_chain_size_is_rejected(count):
    with pytest.raises(ValueError):
        build_mission_segments(count)
