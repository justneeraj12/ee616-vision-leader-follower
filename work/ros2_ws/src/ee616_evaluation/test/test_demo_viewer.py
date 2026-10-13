import numpy as np

from ee616_evaluation.demo_viewer import compose_dashboard


def test_dashboard_contains_one_panel_per_follower():
    image = np.full((480, 640, 3), 127, dtype=np.uint8)
    dashboard = compose_dashboard(
        {1: image, 3: image},
        {1: "TRACK", 2: "PREDICT", 3: "SAFE_STOP"},
        {1: 0.01, 3: 0.02},
        follower_count=3,
        event="LONG_OCCLUSION",
        camera_count=1,
    )
    assert dashboard.shape == (420, 1680, 3)
    assert dashboard.dtype == np.uint8
    assert dashboard.any()
