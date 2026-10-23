"""Focused checks for the warehouse evaluator's static-geometry boundary."""

from ee616_evaluation.warehouse_mission_evaluator import (
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
