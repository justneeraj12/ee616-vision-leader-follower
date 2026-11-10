import math

from ee616_control.control_core import FollowerSupervisor, RelativeEkf


def test_ekf_update_reduces_measurement_error():
    ekf = RelativeEkf()
    ekf.initialize(2.0, 0.1, 0.0)
    before = abs(ekf.x[0] - 1.5)
    ekf.predict(0.1, 0.0, 0.0)
    ekf.update(1.5, 0.0)
    assert abs(ekf.x[0] - 1.5) < before
    assert abs(ekf.x[1]) < 0.1


def test_supervisor_transitions_and_safe_stop():
    supervisor = FollowerSupervisor(track_timeout_s=0.2, predict_timeout_s=0.75)
    assert supervisor.step(0.0, 0.0, 0.0).state == "SAFE_STOP"
    supervisor.accept_measurement(1.8, 0.1, 0.1, 0.0, 0.0)
    tracking = supervisor.step(0.2, 0.0, 0.0)
    assert tracking.state == "TRACK"
    assert tracking.linear_mps > 0.0
    assert tracking.angular_rps > 0.0
    assert supervisor.step(0.5, 0.0, 0.0).state == "PREDICT"
    stopped = supervisor.step(1.0, 0.0, 0.0)
    assert stopped.state == "SAFE_STOP"
    assert stopped.linear_mps == 0.0
    assert stopped.angular_rps == 0.0


def test_commands_are_bounded():
    supervisor = FollowerSupervisor(max_linear_mps=0.5, max_angular_rps=0.7)
    supervisor.accept_measurement(20.0, math.pi / 2.0, 0.0, 0.0, 0.0)
    output = supervisor.step(0.01, 0.0, 0.0)
    assert 0.0 <= output.linear_mps <= 0.5
    assert -0.7 <= output.angular_rps <= 0.7


def test_supervisor_rejects_gross_target_switch():
    supervisor = FollowerSupervisor(innovation_gate_sq=100.0)
    assert supervisor.accept_measurement(1.0, 0.0, 0.0, 0.0, 0.0)
    assert not supervisor.accept_measurement(3.0, 0.0, 0.05, 0.0, 0.0)
    assert supervisor.last_measurement_s == 0.0


def test_supervisor_rejects_measurements_outside_tracking_envelope():
    supervisor = FollowerSupervisor(max_measurement_range_m=2.5)
    assert not supervisor.accept_measurement(3.0, 0.0, 0.0, 0.0, 0.0)
    assert supervisor.step(0.1, 0.0, 0.0).state == "SAFE_STOP"


def test_large_bearing_reduces_forward_command():
    supervisor = FollowerSupervisor(bearing_slowdown_rad=0.5)
    supervisor.accept_measurement(2.0, 0.4, 0.0, 0.0, 0.0)
    output = supervisor.step(0.01, 0.0, 0.0)
    assert 0.0 < output.linear_mps < 0.15
    assert output.angular_rps > 0.0


def test_search_starts_only_after_stopped_and_remains_linear_zero():
    supervisor = FollowerSupervisor(
        track_timeout_s=0.2,
        predict_timeout_s=0.75,
        search_enabled=True,
        search_settle_s=0.25,
        search_angular_rps=0.20,
    )
    assert supervisor.accept_measurement(1.7, 0.3, 0.0, 0.0, 0.0)
    assert supervisor.step(0.1, 0.0, 0.0).state == "TRACK"
    stopping = supervisor.step(0.80, 0.10, 0.0)
    assert stopping.state == "SAFE_STOP"
    assert stopping.linear_mps == 0.0
    assert stopping.angular_rps == 0.0
    still_stopping = supervisor.step(1.10, 0.08, 0.0)
    assert still_stopping.state == "SAFE_STOP"
    searching = supervisor.step(1.15, 0.0, 0.0)
    assert searching.state == "SEARCH"
    assert searching.linear_mps == 0.0
    assert searching.angular_rps == 0.20


def test_search_requires_consistent_reacquisition_before_track():
    supervisor = FollowerSupervisor(
        track_timeout_s=0.25,
        predict_timeout_s=0.75,
        search_enabled=True,
        search_settle_s=0.20,
        reacquire_confirmations=3,
        reacquire_hold_s=0.50,
    )
    assert supervisor.accept_measurement(1.6, -0.2, 0.0, 0.0, 0.0)
    supervisor.step(0.1, 0.0, 0.0)
    supervisor.step(0.8, 0.0, 0.0)
    assert supervisor.step(1.05, 0.0, 0.0).state == "SEARCH"
    assert not supervisor.accept_measurement(1.55, 0.45, 1.10, 0.0, 0.0)
    assert not supervisor.accept_measurement(1.58, 0.47, 1.17, 0.0, 0.0)
    assert supervisor.accept_measurement(1.56, 0.46, 1.24, 0.0, 0.0)
    reacquire = supervisor.step(1.25, 0.0, 0.0)
    assert reacquire.state == "REACQUIRE"
    assert reacquire.linear_mps == 0.0
    assert reacquire.angular_rps == 0.0
    assert supervisor.accept_measurement(1.54, 0.43, 1.50, 0.0, 0.0)
    assert supervisor.accept_measurement(1.53, 0.42, 1.70, 0.0, 0.0)
    resumed = supervisor.step(1.76, 0.0, 0.0)
    assert resumed.state == "TRACK"
    assert 0.0 <= resumed.linear_mps <= supervisor.max_linear_mps


def test_safe_stop_cannot_bypass_search_with_a_visible_panel():
    supervisor = FollowerSupervisor(
        track_timeout_s=0.2,
        predict_timeout_s=0.5,
        search_enabled=True,
        search_settle_s=0.2,
        reacquire_confirmations=3,
    )
    assert supervisor.accept_measurement(1.5, 0.0, 0.0, 0.0, 0.0)
    supervisor.step(0.1, 0.0, 0.0)
    stopped = supervisor.step(0.6, 0.0, 0.0)
    assert stopped.state == "SAFE_STOP"
    assert not supervisor.accept_measurement(3.4, 0.8, 0.61, 0.0, 0.0)
    assert supervisor.step(0.7, 0.0, 0.0).state == "SAFE_STOP"
    assert supervisor.step(0.81, 0.0, 0.0).state == "SEARCH"


def test_first_valid_measurement_enters_track_before_next_camera_frame():
    supervisor = FollowerSupervisor(search_enabled=True)
    assert supervisor.accept_measurement(1.5, 0.0, 0.0, 0.0, 0.0)
    assert supervisor.mode == "TRACK"
    assert supervisor.accept_measurement(1.51, 0.01, 0.05, 0.0, 0.0)
    assert supervisor.step(0.06, 0.0, 0.0).state == "TRACK"


def test_search_times_out_to_latched_safe_stop():
    supervisor = FollowerSupervisor(
        track_timeout_s=0.2,
        predict_timeout_s=0.5,
        search_enabled=True,
        search_settle_s=0.1,
        search_timeout_s=0.6,
    )
    supervisor.accept_measurement(1.5, 0.1, 0.0, 0.0, 0.0)
    supervisor.step(0.1, 0.0, 0.0)
    supervisor.step(0.6, 0.0, 0.0)
    assert supervisor.step(0.75, 0.0, 0.0).state == "SEARCH"
    timed_out = supervisor.step(1.36, 0.0, 0.0)
    assert timed_out.state == "SAFE_STOP"
    assert timed_out.linear_mps == 0.0
    assert timed_out.angular_rps == 0.0
    assert supervisor.step(2.0, 0.0, 0.0).state == "SAFE_STOP"


def test_default_search_timeout_can_scan_both_sides_of_envelope():
    supervisor = FollowerSupervisor(
        track_timeout_s=0.1,
        predict_timeout_s=0.2,
        search_enabled=True,
        search_settle_s=0.0,
    )
    supervisor.accept_measurement(1.5, 0.1, 0.0, 0.0, 0.0)
    supervisor.step(0.05, 0.0, 0.0)
    output = supervisor.step(0.25, 0.0, 0.0)
    assert output.state == "SEARCH"
    minimum_yaw = supervisor.search_yaw_rad
    maximum_yaw = supervisor.search_yaw_rad
    stamp_s = 0.25
    for _ in range(85):
        stamp_s += 0.20
        output = supervisor.step(stamp_s, 0.0, output.angular_rps)
        assert output.state == "SEARCH"
        assert output.linear_mps == 0.0
        assert abs(output.angular_rps) <= supervisor.search_angular_rps
        minimum_yaw = min(minimum_yaw, supervisor.search_yaw_rad)
        maximum_yaw = max(maximum_yaw, supervisor.search_yaw_rad)
    assert maximum_yaw >= supervisor.search_sweep_rad
    assert minimum_yaw <= -supervisor.search_sweep_rad
