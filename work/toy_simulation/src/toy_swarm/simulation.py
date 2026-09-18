from __future__ import annotations

from dataclasses import asdict, dataclass
from math import atan2, cos, pi, sin, sqrt, tan
from time import perf_counter
from typing import Any

import numpy as np


def wrap_angle(value: float) -> float:
    return (value + pi) % (2.0 * pi) - pi


@dataclass(frozen=True)
class Config:
    duration_s: float = 20.0
    dt_s: float = 0.02
    camera_hz: float = 15.0
    image_width_px: int = 640
    focal_length_px: float = 600.0
    leader_marker_height_m: float = 0.60
    bbox_height_noise_px: float = 1.8
    bbox_center_noise_px: float = 1.4
    camera_half_fov_deg: float = 42.0
    camera_min_range_m: float = 0.45
    camera_max_range_m: float = 4.00
    desired_range_m: float = 1.50
    max_linear_mps: float = 1.00
    max_angular_rps: float = 1.40
    prediction_timeout_s: float = 1.50
    occlusion_start_s: float = 8.00
    occlusion_end_s: float = 9.17
    collision_range_m: float = 0.35
    k_range: float = 1.15
    k_bearing: float = 2.20


class ConstantVelocityFilter:
    """Small linear Kalman filter over world-frame leader position and velocity."""

    def __init__(self) -> None:
        self.x = np.zeros(4, dtype=float)
        self.p = np.eye(4, dtype=float) * 10.0
        self.initialized = False

    def initialize(self, position_xy: np.ndarray) -> None:
        self.x[:2] = position_xy
        self.x[2:] = 0.0
        self.p = np.diag([0.04, 0.04, 0.50, 0.50])
        self.initialized = True

    def predict(self, dt_s: float) -> None:
        if not self.initialized:
            return
        f = np.array(
            [[1.0, 0.0, dt_s, 0.0], [0.0, 1.0, 0.0, dt_s], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]],
            dtype=float,
        )
        q = 0.18
        g = np.array([[0.5 * dt_s**2, 0.0], [0.0, 0.5 * dt_s**2], [dt_s, 0.0], [0.0, dt_s]])
        self.x = f @ self.x
        self.p = f @ self.p @ f.T + g @ (np.eye(2) * q**2) @ g.T

    def update(self, position_xy: np.ndarray, measurement_std_m: float) -> None:
        if not self.initialized:
            self.initialize(position_xy)
            return
        h = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]], dtype=float)
        r = np.eye(2) * measurement_std_m**2
        innovation = position_xy - h @ self.x
        s = h @ self.p @ h.T + r
        k = self.p @ h.T @ np.linalg.inv(s)
        self.x = self.x + k @ innovation
        self.p = (np.eye(4) - k @ h) @ self.p


def leader_state(t_s: float, scenario: str) -> tuple[float, float, float, float]:
    x0 = 1.50
    if scenario == "straight":
        return x0 + 0.55 * t_s, 0.0, 0.55, 0.0
    if scenario in {"s_curve", "occlusion"}:
        return x0 + 0.52 * t_s, 0.55 * sin(0.32 * t_s), 0.52, 0.176 * cos(0.32 * t_s)
    if scenario == "turn":
        radius = 3.2
        omega = 0.17
        return x0 + radius * sin(omega * t_s), radius * (1.0 - cos(omega * t_s)), radius * omega * cos(omega * t_s), radius * omega * sin(omega * t_s)
    raise ValueError(f"unknown scenario: {scenario}")


def camera_measurement(
    leader_xy: np.ndarray,
    follower_pose: np.ndarray,
    rng: np.random.Generator,
    cfg: Config,
    occluded: bool = False,
) -> tuple[bool, float, float, float, float]:
    dx = float(leader_xy[0] - follower_pose[0])
    dy = float(leader_xy[1] - follower_pose[1])
    true_range = sqrt(dx * dx + dy * dy)
    true_bearing = wrap_angle(atan2(dy, dx) - float(follower_pose[2]))
    within_view = abs(true_bearing) <= np.deg2rad(cfg.camera_half_fov_deg)
    within_range = cfg.camera_min_range_m <= true_range <= cfg.camera_max_range_m
    if occluded or not within_view or not within_range:
        return False, float("nan"), float("nan"), true_range, true_bearing

    bbox_height = cfg.focal_length_px * cfg.leader_marker_height_m / true_range
    bbox_center = cfg.image_width_px / 2.0 + cfg.focal_length_px * tan(true_bearing)
    noisy_height = max(2.0, bbox_height + rng.normal(0.0, cfg.bbox_height_noise_px))
    noisy_center = bbox_center + rng.normal(0.0, cfg.bbox_center_noise_px)
    measured_range = cfg.focal_length_px * cfg.leader_marker_height_m / noisy_height
    measured_bearing = atan2(noisy_center - cfg.image_width_px / 2.0, cfg.focal_length_px)
    return True, measured_range, measured_bearing, true_range, true_bearing


def command_from_estimate(
    follower_pose: np.ndarray,
    estimate: ConstantVelocityFilter,
    time_since_detection_s: float,
    cfg: Config,
) -> tuple[float, float, str, float, float]:
    if not estimate.initialized:
        return 0.0, 0.0, "SAFE_STOP", float("nan"), float("nan")
    dx = float(estimate.x[0] - follower_pose[0])
    dy = float(estimate.x[1] - follower_pose[1])
    range_est = sqrt(dx * dx + dy * dy)
    bearing_est = wrap_angle(atan2(dy, dx) - float(follower_pose[2]))
    if time_since_detection_s > cfg.prediction_timeout_s:
        return 0.0, 0.0, "SAFE_STOP", range_est, bearing_est
    state = "TRACK" if time_since_detection_s <= (1.0 / cfg.camera_hz + cfg.dt_s) else "PREDICT"
    leader_forward_speed = max(0.0, float(estimate.x[2] * cos(follower_pose[2]) + estimate.x[3] * sin(follower_pose[2])))
    linear = leader_forward_speed * max(0.0, cos(bearing_est)) + cfg.k_range * (range_est - cfg.desired_range_m)
    linear = float(np.clip(linear, 0.0, cfg.max_linear_mps))
    angular = float(np.clip(cfg.k_bearing * bearing_est, -cfg.max_angular_rps, cfg.max_angular_rps))
    return linear, angular, state, range_est, bearing_est


def simulate_trial(seed: int, scenario: str, cfg: Config | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cfg = cfg or Config()
    rng = np.random.default_rng(seed)
    follower = np.array([0.0, 0.0, 0.0], dtype=float)
    estimate = ConstantVelocityFilter()
    last_detection_t = -1e9
    next_camera_t = 0.0
    rows: list[dict[str, Any]] = []
    camera_cost_ms: list[float] = []
    detection_times: list[float] = []

    steps = int(round(cfg.duration_s / cfg.dt_s)) + 1
    for step in range(steps):
        t_s = step * cfg.dt_s
        lx, ly, lvx, lvy = leader_state(t_s, scenario)
        estimate.predict(cfg.dt_s)
        detection = False
        measured_range = measured_bearing = float("nan")
        true_dx = lx - follower[0]
        true_dy = ly - follower[1]
        true_range = sqrt(true_dx * true_dx + true_dy * true_dy)
        true_bearing = wrap_angle(atan2(true_dy, true_dx) - follower[2])

        if t_s + 1e-12 >= next_camera_t:
            start = perf_counter()
            occluded = scenario == "occlusion" and cfg.occlusion_start_s <= t_s < cfg.occlusion_end_s
            detection, measured_range, measured_bearing, true_range, true_bearing = camera_measurement(
                np.array([lx, ly]), follower, rng, cfg, occluded=occluded
            )
            camera_cost_ms.append((perf_counter() - start) * 1000.0)
            next_camera_t += 1.0 / cfg.camera_hz
            if detection:
                direction = follower[2] + measured_bearing
                measured_world = np.array(
                    [follower[0] + measured_range * cos(direction), follower[1] + measured_range * sin(direction)]
                )
                estimate.update(measured_world, measurement_std_m=0.045 + 0.012 * measured_range)
                last_detection_t = t_s
                detection_times.append(t_s)

        since_detection = t_s - last_detection_t
        linear, angular, control_state, estimated_range, estimated_bearing = command_from_estimate(
            follower, estimate, since_detection, cfg
        )
        follower[0] += linear * cos(follower[2]) * cfg.dt_s
        follower[1] += linear * sin(follower[2]) * cfg.dt_s
        follower[2] = wrap_angle(follower[2] + angular * cfg.dt_s)
        collision = true_range < cfg.collision_range_m

        rows.append(
            {
                "time_s": t_s,
                "seed": seed,
                "scenario": scenario,
                "leader_x_m": lx,
                "leader_y_m": ly,
                "leader_vx_mps": lvx,
                "leader_vy_mps": lvy,
                "follower_x_m": float(follower[0]),
                "follower_y_m": float(follower[1]),
                "follower_yaw_rad": float(follower[2]),
                "true_range_m": true_range,
                "true_bearing_rad": true_bearing,
                "detection": int(detection),
                "measured_range_m": measured_range,
                "measured_bearing_rad": measured_bearing,
                "estimated_range_m": estimated_range,
                "estimated_bearing_rad": estimated_bearing,
                "linear_cmd_mps": linear,
                "angular_cmd_rps": angular,
                "control_state": control_state,
                "collision": int(collision),
            }
        )

    detected = [row for row in rows if row["detection"]]
    steady = [row for row in rows if row["time_s"] >= 4.0 and np.isfinite(row["estimated_range_m"])]
    range_errors = np.array([row["measured_range_m"] - row["true_range_m"] for row in detected])
    bearing_errors = np.array([wrap_angle(row["measured_bearing_rad"] - row["true_bearing_rad"]) for row in detected])
    estimate_errors = np.array([row["estimated_range_m"] - row["true_range_m"] for row in steady])
    formation_errors = np.array([row["true_range_m"] - cfg.desired_range_m for row in steady])
    reacquisition_s = float("nan")
    if scenario == "occlusion":
        after = [value for value in detection_times if value >= cfg.occlusion_end_s]
        if after:
            reacquisition_s = after[0] - cfg.occlusion_end_s

    metrics = {
        "seed": seed,
        "scenario": scenario,
        "samples": len(rows),
        "detections": len(detected),
        "range_rmse_m": float(np.sqrt(np.mean(range_errors**2))),
        "bearing_mae_deg": float(np.rad2deg(np.mean(np.abs(bearing_errors)))),
        "estimated_range_rmse_m": float(np.sqrt(np.mean(estimate_errors**2))),
        "formation_rmse_m": float(np.sqrt(np.mean(formation_errors**2))),
        "collision_samples": int(sum(row["collision"] for row in rows)),
        "safe_stop_fraction": float(np.mean([row["control_state"] == "SAFE_STOP" for row in rows])),
        "reacquisition_s": reacquisition_s,
        "camera_model_p95_ms": float(np.percentile(camera_cost_ms, 95)),
        "config": asdict(cfg),
    }
    return rows, metrics
