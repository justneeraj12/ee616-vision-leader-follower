"""Pure estimation, control, and supervisor logic for one follower."""

from __future__ import annotations

import math
from dataclasses import dataclass

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

    def update(
        self,
        range_m: float,
        bearing_rad: float,
        *,
        max_mahalanobis_sq: float = math.inf,
    ) -> bool:
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
        inverse_s = np.linalg.inv(s)
        mahalanobis_sq = float(innovation.T @ inverse_s @ innovation)
        if mahalanobis_sq > max_mahalanobis_sq:
            return False
        gain = self.p @ h.T @ inverse_s
        self.x += gain @ innovation
        self.x[0] = max(0.05, self.x[0])
        self.x[1] = wrap_angle(float(self.x[1]))
        self.p = (np.eye(4) - gain @ h) @ self.p
        return True


class FollowerSupervisor:
    """Bounded tracking supervisor with optional visual search recovery."""

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
        innovation_gate_sq: float = 100.0,
        max_measurement_range_m: float = 30.0,
        bearing_slowdown_rad: float = 0.0,
        search_enabled: bool = False,
        search_settle_s: float = 0.25,
        search_angular_rps: float = 0.20,
        search_sweep_rad: float = math.radians(60.0),
        search_timeout_s: float = 18.0,
        search_stop_linear_mps: float = 0.03,
        search_stop_angular_rps: float = 0.05,
        reacquire_confirmations: int = 3,
        reacquire_hold_s: float = 0.50,
        reacquire_range_tolerance_m: float = 0.75,
    ) -> None:
        if not 0.0 < track_timeout_s < predict_timeout_s:
            raise ValueError("timeouts must satisfy 0 < track < predict")
        if innovation_gate_sq <= 0.0:
            raise ValueError("innovation_gate_sq must be positive")
        if max_measurement_range_m <= desired_range_m:
            raise ValueError("max_measurement_range_m must exceed desired_range_m")
        if bearing_slowdown_rad < 0.0:
            raise ValueError("bearing_slowdown_rad must be nonnegative")
        if search_settle_s < 0.0:
            raise ValueError("search_settle_s must be nonnegative")
        if not 0.0 < search_angular_rps <= max_angular_rps:
            raise ValueError("search_angular_rps must be positive and bounded")
        if not 0.0 < search_sweep_rad <= math.pi:
            raise ValueError("search_sweep_rad must be in (0, pi]")
        if search_timeout_s <= search_settle_s:
            raise ValueError("search_timeout_s must exceed search_settle_s")
        if search_stop_linear_mps < 0.0 or search_stop_angular_rps < 0.0:
            raise ValueError("search stop thresholds must be nonnegative")
        if reacquire_confirmations < 2:
            raise ValueError("reacquire_confirmations must be at least two")
        if reacquire_hold_s < 0.0:
            raise ValueError("reacquire_hold_s must be nonnegative")
        if reacquire_range_tolerance_m <= 0.0:
            raise ValueError("reacquire_range_tolerance_m must be positive")
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
        self.innovation_gate_sq = innovation_gate_sq
        self.max_measurement_range_m = max_measurement_range_m
        self.bearing_slowdown_rad = bearing_slowdown_rad
        self.search_enabled = bool(search_enabled)
        self.search_settle_s = search_settle_s
        self.search_angular_rps = search_angular_rps
        self.search_sweep_rad = search_sweep_rad
        self.search_timeout_s = search_timeout_s
        self.search_stop_linear_mps = search_stop_linear_mps
        self.search_stop_angular_rps = search_stop_angular_rps
        self.reacquire_confirmations = int(reacquire_confirmations)
        self.reacquire_hold_s = reacquire_hold_s
        self.reacquire_range_tolerance_m = reacquire_range_tolerance_m
        self.ekf = RelativeEkf()
        self.last_measurement_s: float | None = None
        self.mode = "SAFE_STOP"
        self.ever_tracked = False
        self.safe_stop_started_s: float | None = None
        self.search_started_s: float | None = None
        self.search_yaw_rad = 0.0
        self.search_direction = 1.0
        self.search_exhausted = False
        self.reacquired_s: float | None = None
        self.last_step_s: float | None = None
        self.candidate_range_m: float | None = None
        self.candidate_bearing_rad: float | None = None
        self.candidate_stamp_s: float | None = None
        self.candidate_count = 0

    def _reset_candidate(self) -> None:
        self.candidate_range_m = None
        self.candidate_bearing_rad = None
        self.candidate_stamp_s = None
        self.candidate_count = 0

    def _candidate_is_consistent(
        self,
        range_m: float,
        bearing_rad: float,
        stamp_s: float,
    ) -> bool:
        if (
            self.candidate_range_m is None
            or self.candidate_bearing_rad is None
            or self.candidate_stamp_s is None
        ):
            return False
        return (
            0.0 <= stamp_s - self.candidate_stamp_s <= 0.35
            and abs(range_m - self.candidate_range_m) <= 0.20
            and abs(wrap_angle(bearing_rad - self.candidate_bearing_rad))
            <= math.radians(8.0)
        )

    def _accept_reacquisition_candidate(
        self,
        range_m: float,
        bearing_rad: float,
        stamp_s: float,
    ) -> bool:
        if (
            self.ekf.initialized
            and abs(range_m - float(self.ekf.x[0]))
            > self.reacquire_range_tolerance_m
        ):
            self._reset_candidate()
            return False
        if self._candidate_is_consistent(range_m, bearing_rad, stamp_s):
            self.candidate_count += 1
        else:
            self.candidate_count = 1
        self.candidate_range_m = range_m
        self.candidate_bearing_rad = wrap_angle(bearing_rad)
        self.candidate_stamp_s = stamp_s
        if self.candidate_count < self.reacquire_confirmations:
            return False
        self.ekf.initialize(range_m, bearing_rad, stamp_s)
        self.last_measurement_s = stamp_s
        self.mode = "REACQUIRE"
        self.reacquired_s = stamp_s
        self.search_exhausted = False
        self._reset_candidate()
        return True

    def accept_measurement(
        self,
        range_m: float,
        bearing_rad: float,
        stamp_s: float,
        follower_v: float,
        follower_w: float,
    ) -> bool:
        if (
            not math.isfinite(range_m)
            or not math.isfinite(bearing_rad)
            or not 0.0 < range_m <= self.max_measurement_range_m
        ):
            return False
        if self.search_enabled and self.ever_tracked and self.mode == "SAFE_STOP":
            # A stopped follower must begin the bounded scan before it may
            # confirm a target.  This prevents an off-axis panel visible at
            # the instant of stopping from bypassing SEARCH.
            return False
        if self.search_enabled and self.ever_tracked and self.mode == "SEARCH":
            return self._accept_reacquisition_candidate(
                range_m, bearing_rad, stamp_s
            )
        if not self.ekf.initialized:
            self.ekf.initialize(range_m, bearing_rad, stamp_s)
            accepted = True
            # The first valid target establishes the initial track.  Without
            # this transition, a second camera frame can be mistaken for a
            # post-loss SAFE_STOP candidate before the control timer runs.
            self.mode = "TRACK"
        else:
            self.ekf.predict(stamp_s, follower_v, follower_w)
            accepted = self.ekf.update(
                range_m,
                bearing_rad,
                max_mahalanobis_sq=self.innovation_gate_sq,
            )
        if not accepted:
            return False
        self.last_measurement_s = stamp_s
        self.ever_tracked = True
        return True

    def _enter_safe_stop(self, stamp_s: float, bearing_rad: float) -> None:
        self.mode = "SAFE_STOP"
        self.safe_stop_started_s = stamp_s
        self.search_started_s = None
        self.search_yaw_rad = 0.0
        self.search_direction = 1.0 if bearing_rad >= 0.0 else -1.0
        self.search_exhausted = False
        self.reacquired_s = None
        self._reset_candidate()

    def _start_search(self, stamp_s: float) -> None:
        self.mode = "SEARCH"
        self.search_started_s = stamp_s
        self.search_yaw_rad = 0.0

    def _search_output(
        self,
        stamp_s: float,
        follower_w: float,
        dt: float,
        range_m: float,
        bearing_rad: float,
        age_s: float,
    ) -> ControlOutput:
        self.search_yaw_rad = wrap_angle(
            self.search_yaw_rad + follower_w * dt
        )
        if self.search_yaw_rad >= self.search_sweep_rad:
            self.search_direction = -1.0
        elif self.search_yaw_rad <= -self.search_sweep_rad:
            self.search_direction = 1.0
        if (
            self.search_started_s is None
            or stamp_s - self.search_started_s >= self.search_timeout_s
        ):
            self.mode = "SAFE_STOP"
            self.search_exhausted = True
            return ControlOutput(
                "SAFE_STOP", 0.0, 0.0, range_m, bearing_rad, age_s
            )
        return ControlOutput(
            "SEARCH",
            0.0,
            self.search_direction * self.search_angular_rps,
            range_m,
            bearing_rad,
            age_s,
        )

    def _tracking_output(
        self,
        state: str,
        range_m: float,
        bearing: float,
        range_rate: float,
        bearing_rate: float,
        age: float,
    ) -> ControlOutput:
        linear = self.range_rate_gain * range_rate
        linear += self.range_gain * (range_m - self.desired_range_m)
        angular = self.bearing_gain * bearing
        angular += self.bearing_rate_gain * bearing_rate
        linear = max(0.0, min(self.max_linear_mps, linear))
        angular = max(-self.max_angular_rps, min(self.max_angular_rps, angular))
        if self.bearing_slowdown_rad > 0.0:
            alignment = max(
                0.0,
                1.0 - abs(bearing) / self.bearing_slowdown_rad,
            )
            linear *= alignment
        if state == "PREDICT":
            linear *= self.predict_speed_scale
        return ControlOutput(state, linear, angular, range_m, bearing, age)

    def step(self, stamp_s: float, follower_v: float, follower_w: float) -> ControlOutput:
        dt = (
            max(0.0, min(0.20, stamp_s - self.last_step_s))
            if self.last_step_s is not None else 0.0
        )
        self.last_step_s = stamp_s
        self.ekf.predict(stamp_s, follower_v, follower_w)
        if not self.ekf.initialized or self.last_measurement_s is None:
            return ControlOutput("SAFE_STOP", 0.0, 0.0, math.nan, math.nan, math.inf)
        age = max(0.0, stamp_s - self.last_measurement_s)
        range_m, bearing, range_rate, bearing_rate = self.ekf.x
        range_m = float(range_m)
        bearing = float(bearing)
        range_rate = float(range_rate)
        bearing_rate = float(bearing_rate)
        if self.search_enabled and self.mode == "REACQUIRE":
            if age > self.track_timeout_s:
                self._enter_safe_stop(stamp_s, bearing)
                return ControlOutput(
                    "SAFE_STOP", 0.0, 0.0, range_m, bearing, age
                )
            if (
                self.reacquired_s is not None
                and stamp_s - self.reacquired_s < self.reacquire_hold_s
            ):
                return ControlOutput(
                    "REACQUIRE", 0.0, 0.0, range_m, bearing, age
                )
            self.mode = "TRACK"
        if self.search_enabled and self.mode == "SEARCH":
            return self._search_output(
                stamp_s, follower_w, dt, range_m, bearing, age
            )
        if age > self.predict_timeout_s:
            if not self.search_enabled:
                return ControlOutput(
                    "SAFE_STOP", 0.0, 0.0, range_m, bearing, age
                )
            if self.mode not in {"SAFE_STOP", "SEARCH"}:
                self._enter_safe_stop(stamp_s, bearing)
            if (
                not self.search_exhausted
                and self.ever_tracked
                and self.safe_stop_started_s is not None
                and stamp_s - self.safe_stop_started_s >= self.search_settle_s
                and abs(follower_v) <= self.search_stop_linear_mps
                and abs(follower_w) <= self.search_stop_angular_rps
            ):
                self._start_search(stamp_s)
                return self._search_output(
                    stamp_s, follower_w, dt, range_m, bearing, age
                )
            return ControlOutput(
                "SAFE_STOP", 0.0, 0.0, range_m, bearing, age
            )
        state = "TRACK" if age <= self.track_timeout_s else "PREDICT"
        self.mode = state
        if state == "TRACK":
            self.safe_stop_started_s = None
            self.search_started_s = None
            self.search_exhausted = False
            self._reset_candidate()
        return self._tracking_output(
            state, range_m, bearing, range_rate, bearing_rate, age
        )
