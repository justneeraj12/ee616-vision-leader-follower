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
