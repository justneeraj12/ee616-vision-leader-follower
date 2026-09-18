import math
import unittest

import numpy as np

from toy_swarm.simulation import Config, ConstantVelocityFilter, camera_measurement, command_from_estimate, simulate_trial
from toy_swarm.warehouse import line_of_sight_clear, simulate_warehouse


class ToySimulationTests(unittest.TestCase):
    def test_noise_free_camera_geometry(self):
        cfg = Config(bbox_height_noise_px=0.0, bbox_center_noise_px=0.0)
        detected, measured_range, measured_bearing, true_range, true_bearing = camera_measurement(
            np.array([2.0, 0.4]), np.array([0.0, 0.0, 0.0]), np.random.default_rng(1), cfg
        )
        self.assertTrue(detected)
        self.assertAlmostEqual(measured_range, true_range, places=10)
        self.assertAlmostEqual(measured_bearing, true_bearing, places=10)

    def test_filter_prediction_advances_position(self):
        filt = ConstantVelocityFilter()
        filt.initialize(np.array([1.0, 2.0]))
        filt.x[2:] = [0.5, -0.25]
        filt.predict(2.0)
        np.testing.assert_allclose(filt.x[:2], [2.0, 1.5], atol=1e-12)

    def test_controller_safe_stops_after_timeout(self):
        cfg = Config(prediction_timeout_s=1.5)
        filt = ConstantVelocityFilter()
        filt.initialize(np.array([2.0, 0.0]))
        linear, angular, state, _, _ = command_from_estimate(np.zeros(3), filt, 1.51, cfg)
        self.assertEqual(state, "SAFE_STOP")
        self.assertEqual(linear, 0.0)
        self.assertEqual(angular, 0.0)

    def test_seed_is_deterministic(self):
        rows_a, metrics_a = simulate_trial(3, "occlusion")
        rows_b, metrics_b = simulate_trial(3, "occlusion")
        self.assertEqual(metrics_a["range_rmse_m"], metrics_b["range_rmse_m"])
        self.assertEqual(rows_a[200]["measured_range_m"], rows_b[200]["measured_range_m"])

    def test_trial_outputs_are_finite(self):
        _, metrics = simulate_trial(0, "s_curve")
        for key in ("range_rmse_m", "bearing_mae_deg", "estimated_range_rmse_m", "formation_rmse_m"):
            self.assertTrue(math.isfinite(metrics[key]), key)

    def test_shelf_blocks_line_of_sight(self):
        self.assertFalse(line_of_sight_clear(np.array([1.0, 2.8, 0.0]), np.array([7.2, 2.8, 0.0])))

    def test_multi_follower_warehouse_is_deterministic(self):
        rows_a, summary_a = simulate_warehouse(seed=5)
        rows_b, summary_b = simulate_warehouse(seed=5)
        self.assertEqual(summary_a, summary_b)
        self.assertEqual(rows_a[1000]['r3_x_m'], rows_b[1000]['r3_x_m'])


if __name__ == "__main__":
    unittest.main()
