"""Pure estimation, control, and supervisor logic for one follower."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


def wrap_angle(value: float) -> float:
    """Wrap an angle to [-pi, pi)."""
    return (value + math.pi) % (2.0 * math.pi) - math.pi


@dataclass(frozen=True)
class ControlOutput:
    """One bounded supervisor output."""

    state: str
    linear_mps: float
    angular_rps: float
    range_m: float
    bearing_rad: float
    measurement_age_s: float


class RelativeEkf:
    """EKF for relative range, bearing, and their predecessor-driven rates."""

    def __init__(self) -> None:
        self.x = np.zeros(4, dtype=float)
        self.p = np.diag([0.20**2, math.radians(8.0) ** 2, 0.25**2, 0.20**2])
        self.initialized = False
        self.stamp_s: float | None = None

    def initialize(self, range_m: float, bearing_rad: float, stamp_s: float) -> None:
        self.x[:] = [range_m, wrap_angle(bearing_rad), 0.0, 0.0]
        self.p = np.diag([0.08**2, math.radians(2.0) ** 2, 0.25**2, 0.20**2])
        self.initialized = True
        self.stamp_s = stamp_s

    def predict(self, stamp_s: float, follower_v: float, follower_w: float) -> None:
        if not self.initialized:
            self.stamp_s = stamp_s
            return
        if self.stamp_s is None:
            self.stamp_s = stamp_s
            return
        dt = max(0.0, min(0.20, stamp_s - self.stamp_s))
        self.stamp_s = stamp_s
        if dt <= 0.0:
            return
        range_m = max(0.05, float(self.x[0]))
        bearing = float(self.x[1])
        range_rate = float(self.x[2])
        bearing_rate = float(self.x[3])
        cosine = math.cos(bearing)
        sine = math.sin(bearing)
        self.x[0] = max(0.05, range_m + (range_rate - follower_v * cosine) * dt)
        self.x[1] = wrap_angle(
            bearing
            + (bearing_rate + follower_v * sine / range_m - follower_w) * dt
        )
        f = np.eye(4, dtype=float)
        f[0, 1] = follower_v * sine * dt
        f[0, 2] = dt
        f[1, 0] = -follower_v * sine * dt / (range_m * range_m)
        f[1, 1] += follower_v * cosine * dt / range_m
        f[1, 3] = dt
        q = np.diag([0.015**2, math.radians(0.8) ** 2, 0.12**2, 0.10**2]) * dt
        self.p = f @ self.p @ f.T + q

    def update(self, range_m: float, bearing_rad: float) -> None:
        if not self.initialized:
            raise RuntimeError("EKF must be initialized before update")
        h = np.zeros((2, 4), dtype=float)
        h[0, 0] = 1.0
        h[1, 1] = 1.0
        innovation = np.array(
            [range_m - self.x[0], wrap_angle(bearing_rad - self.x[1])],
            dtype=float,
        )
        r = np.diag([0.04**2, math.radians(0.5) ** 2])
        s = h @ self.p @ h.T + r
        gain = self.p @ h.T @ np.linalg.inv(s)
        self.x += gain @ innovation
        self.x[0] = max(0.05, self.x[0])
        self.x[1] = wrap_angle(float(self.x[1]))
        self.p = (np.eye(4) - gain @ h) @ self.p


class FollowerSupervisor:
    """TRACK, PREDICT, and SAFE_STOP supervisor with bounded commands."""

    def __init__(
        self,
        *,
        desired_range_m: float = 1.5,
        max_linear_mps: float = 0.6,
        max_angular_rps: float = 0.8,
        track_timeout_s: float = 0.2,
        predict_timeout_s: float = 0.75,
        range_gain: float = 0.85,
        range_rate_gain: float = 0.85,
        bearing_gain: float = 1.8,
        bearing_rate_gain: float = 0.2,
        predict_speed_scale: float = 0.55,
    ) -> None:
        if not 0.0 < track_timeout_s < predict_timeout_s:
            raise ValueError("timeouts must satisfy 0 < track < predict")
        self.desired_range_m = desired_range_m
        self.max_linear_mps = max_linear_mps
        self.max_angular_rps = max_angular_rps
        self.track_timeout_s = track_timeout_s
        self.predict_timeout_s = predict_timeout_s
        self.range_gain = range_gain
        self.range_rate_gain = range_rate_gain
        self.bearing_gain = bearing_gain
        self.bearing_rate_gain = bearing_rate_gain
        self.predict_speed_scale = predict_speed_scale
        self.ekf = RelativeEkf()
        self.last_measurement_s: float | None = None

    def accept_measurement(
        self,
        range_m: float,
        bearing_rad: float,
        stamp_s: float,
        follower_v: float,
        follower_w: float,
    ) -> None:
        if not math.isfinite(range_m) or not math.isfinite(bearing_rad) or range_m <= 0.0:
            return
        if not self.ekf.initialized:
            self.ekf.initialize(range_m, bearing_rad, stamp_s)
        else:
            self.ekf.predict(stamp_s, follower_v, follower_w)
            self.ekf.update(range_m, bearing_rad)
        self.last_measurement_s = stamp_s

    def step(self, stamp_s: float, follower_v: float, follower_w: float) -> ControlOutput:
        self.ekf.predict(stamp_s, follower_v, follower_w)
        if not self.ekf.initialized or self.last_measurement_s is None:
            return ControlOutput("SAFE_STOP", 0.0, 0.0, math.nan, math.nan, math.inf)
        age = max(0.0, stamp_s - self.last_measurement_s)
        range_m, bearing, range_rate, bearing_rate = self.ekf.x
        if age > self.predict_timeout_s:
            return ControlOutput("SAFE_STOP", 0.0, 0.0, float(range_m), float(bearing), age)
        state = "TRACK" if age <= self.track_timeout_s else "PREDICT"
        linear = self.range_rate_gain * float(range_rate)
        linear += self.range_gain * (float(range_m) - self.desired_range_m)
        angular = self.bearing_gain * float(bearing)
        angular += self.bearing_rate_gain * float(bearing_rate)
        linear = max(0.0, min(self.max_linear_mps, linear))
        angular = max(-self.max_angular_rps, min(self.max_angular_rps, angular))
        if state == "PREDICT":
            linear *= self.predict_speed_scale
        return ControlOutput(state, linear, angular, float(range_m), float(bearing), age)
