from ee616_simulation.disturbance_proxy import disturbed_command, scheduled_event


def test_event_schedule_is_fixed_and_bounded():
    assert scheduled_event("short_occlusion", 9.25) == "SHORT_OCCLUSION"
    assert scheduled_event("short_occlusion", 9.75) == "NONE"
    assert scheduled_event("combined", 12.5) == "LONG_OCCLUSION"
    assert scheduled_event("combined", 34.25) == "ACTUATOR_BIAS"
    assert scheduled_event("long_occlusion", 12.5, schedule_delay_s=4.0) == "NONE"
    assert scheduled_event("long_occlusion", 13.5, schedule_delay_s=4.0) == "LONG_OCCLUSION"


def test_actuator_bias_remains_bounded():
    linear, angular = disturbed_command(0.7, 0.75, "ACTUATOR_BIAS")
    assert linear == 0.6
    assert angular == 0.8
