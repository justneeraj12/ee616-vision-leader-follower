from ee616_dashboard.experiment_console import (
    failure_explanation,
    summarize_result,
)


def test_error_105_has_readable_explanation():
    explanation = failure_explanation("regulated path tracking failed: 105")
    assert "FAILED_TO_MAKE_PROGRESS" in explanation
    assert "progress checker" in explanation


def test_failed_held_mission_is_contained_not_passed():
    result = summarize_result({
        "status": "fail",
        "failure": "regulated path tracking failed: 105",
        "mission_checks": {"route_complete": False},
        "followers": {"1": {"collision_samples": 0}},
        "warehouse_obstacle_collision_samples": {"leader": 0},
        "governor": {"final_state": {"mode": "HOLD"}},
    })
    assert result["outcome"] == "CONTAINED"
    assert not result["route_complete"]


def test_pass_requires_route_completion():
    result = summarize_result({
        "status": "pass",
        "mission_checks": {"route_complete": True},
        "followers": {},
        "warehouse_obstacle_collision_samples": {},
        "governor": {"final_state": {"mode": "NORMAL"}},
    })
    assert result["outcome"] == "PASS"


def test_completed_route_with_failed_metric_is_limited_not_passed():
    result = summarize_result({
        "status": "fail",
        "mission_checks": {"route_complete": True},
        "followers": {"2": {"collision_samples": 0}},
        "warehouse_obstacle_collision_samples": {"leader": 0},
        "governor": {"final_state": {"mode": "MISSION"}},
    })
    assert result["outcome"] == "LIMITED"


def test_hold_without_collision_evidence_is_not_contained():
    result = summarize_result({
        "status": "fail",
        "mission_checks": {"route_complete": False},
        "followers": {},
        "warehouse_obstacle_collision_samples": {},
        "governor": {"final_state": {"mode": "HOLD"}},
    })
    assert result["outcome"] == "FAILED"
