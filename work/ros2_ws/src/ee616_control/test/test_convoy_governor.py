from ee616_control.convoy_governor import (
    FollowerHealth,
    decide_governor,
)


def health(state="TRACK", bearing=0.0, measurement_age=0.02, telemetry_age=0.02):
    return FollowerHealth(state, bearing, measurement_age, telemetry_age)


def test_loading_commands_pass_without_navigation_health_gate():
    decision = decide_governor([], mission_state="LOAD_LEADER")
    assert decision.mode == "MISSION"
    assert not decision.hold


def test_predict_and_large_bearing_request_caution():
    predict = decide_governor([health(state="PREDICT")], mission_state="NAV_AISLE")
    bearing = decide_governor([health(bearing=0.5)], mission_state="NAV_AISLE")
    assert predict.mode == "CAUTION"
    assert not predict.hold
    assert 0.0 < predict.linear_scale < 1.0
    assert bearing.mode == "CAUTION"
    assert 0.0 < bearing.linear_scale < 1.0


def test_safe_stop_stale_health_and_fault_hold_leader():
    safe = decide_governor([health(state="SAFE_STOP")], mission_state="NAV_AISLE")
    stale = decide_governor(
        [health(telemetry_age=1.0)], mission_state="NAV_AISLE"
    )
    fault = decide_governor(
        [health()], mission_state="NAV_AISLE", fault_active=True
    )
    assert safe.hold and safe.mode == "HOLD"
    assert stale.hold and stale.mode == "HOLD"
    assert fault.hold and fault.mode == "FAULT_HOLD"


def test_all_tracking_is_normal_and_never_uses_truth():
    decision = decide_governor(
        [health(), health(), health()], mission_state="NAV_AISLE"
    )
    assert decision.mode == "NORMAL"
    assert decision.linear_scale == 1.0
    assert not decision.hold
