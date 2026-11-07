"""Focused checks for the warehouse evaluator's static-geometry boundary."""

from ee616_evaluation.warehouse_mission_evaluator import (
    route_segment_metrics,
    warehouse_obstacle_collision,
)


def test_clear_aisle_points_do_not_collide():
    assert not warehouse_obstacle_collision(-10.0, -6.0)
    assert not warehouse_obstacle_collision(0.0, -1.0)
    assert not warehouse_obstacle_collision(10.0, 4.75)


def test_shelf_footprint_and_clearance_are_detected():
    assert warehouse_obstacle_collision(0.0, 2.0)
    assert warehouse_obstacle_collision(2.30, 2.0)
    assert not warehouse_obstacle_collision(5.50, 2.0)


def test_perimeter_wall_clearance_is_detected():
    assert warehouse_obstacle_collision(18.40, 0.0)
    assert warehouse_obstacle_collision(0.0, -11.40)
    assert not warehouse_obstacle_collision(18.0, 0.0)


def test_route_segment_metrics_separate_followers_and_supervisor_states():
    rows = [
        {
            "follower_index": 1,
            "mission_state": "NAV_AISLE_1",
            "spacing_error_m": error,
            "control_state": state,
        }
        for error, state in [(0.1, "TRACK"), (-0.1, "PREDICT")]
    ] + [
        {
            "follower_index": 2,
            "mission_state": "NAV_AISLE_1",
            "spacing_error_m": 0.2,
            "control_state": "SAFE_STOP",
        }
    ]
    metrics = route_segment_metrics(rows, 2)
    assert metrics["1"]["NAV_AISLE_1"]["spacing_rmse_m"] == 0.1
    assert metrics["1"]["NAV_AISLE_1"]["track_fraction"] == 0.5
    assert metrics["1"]["NAV_AISLE_1"]["predict_fraction"] == 0.5
    assert metrics["2"]["NAV_AISLE_1"]["safe_stop_fraction"] == 1.0
