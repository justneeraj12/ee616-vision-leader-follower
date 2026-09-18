from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, hypot, pi, sin
from typing import Any

import numpy as np

from .simulation import ConstantVelocityFilter, wrap_angle


SHELVES = (
    (1.5, 2.2, 6.8, 3.4), (9.2, 2.2, 14.5, 3.4),
    (1.5, 4.9, 6.8, 6.1), (9.2, 4.9, 14.5, 6.1),
    (1.5, 7.6, 6.8, 8.6), (9.2, 7.6, 14.5, 8.6),
)

WAYPOINTS = (
    (2.4, 1.2), (15.2, 1.2), (15.2, 4.1), (8.0, 4.1),
    (8.0, 6.85), (15.2, 6.85), (15.2, 9.25), (0.8, 9.25),
)


@dataclass(frozen=True)
class WarehouseConfig:
    dt_s: float = 0.02
    duration_s: float = 86.0
    camera_hz: float = 15.0
    camera_half_fov_deg: float = 58.0
    camera_max_range_m: float = 3.0
    focal_px: float = 600.0
    marker_height_m: float = 0.48
    bbox_height_noise_px: float = 2.2
    bbox_center_noise_px: float = 1.8
    desired_spacing_m: float = 0.80
    robot_radius_m: float = 0.18
    prediction_timeout_s: float = 1.50
    leader_speed_mps: float = 0.65
    follower_max_speed_mps: float = 0.85
    max_angular_rps: float = 1.35


def point_in_rect(x: float, y: float, rect: tuple[float, float, float, float], margin: float = 0.0) -> bool:
    x1, y1, x2, y2 = rect
    return x1 - margin <= x <= x2 + margin and y1 - margin <= y <= y2 + margin


def line_of_sight_clear(a: np.ndarray, b: np.ndarray) -> bool:
    for fraction in np.linspace(0.04, 0.96, 25):
        x, y = a[:2] + fraction * (b[:2] - a[:2])
        if any(point_in_rect(float(x), float(y), rect) for rect in SHELVES):
            return False
    return True


def leader_command(pose: np.ndarray, waypoint_index: int, cfg: WarehouseConfig) -> tuple[float, float, int]:
    while waypoint_index < len(WAYPOINTS) - 1:
        tx, ty = WAYPOINTS[waypoint_index]
        if hypot(tx - pose[0], ty - pose[1]) >= 0.28:
            break
        waypoint_index += 1
    tx, ty = WAYPOINTS[waypoint_index]
    distance = hypot(tx - pose[0], ty - pose[1])
    bearing = wrap_angle(atan2(ty - pose[1], tx - pose[0]) - pose[2])
    angular = float(np.clip(2.2 * bearing, -cfg.max_angular_rps, cfg.max_angular_rps))
    alignment = max(0.0, cos(bearing))
    linear = min(cfg.leader_speed_mps, 0.8 * distance) * alignment
    if waypoint_index == len(WAYPOINTS) - 1 and distance < 0.25:
        linear = 0.0
        angular = 0.0
    return linear, angular, waypoint_index


def camera_observation(
    target: np.ndarray,
    follower: np.ndarray,
    rng: np.random.Generator,
    cfg: WarehouseConfig,
) -> tuple[bool, float, float, str]:
    dx, dy = target[0] - follower[0], target[1] - follower[1]
    distance = hypot(dx, dy)
    bearing = wrap_angle(atan2(dy, dx) - follower[2])
    if not line_of_sight_clear(follower, target):
        return False, float('nan'), float('nan'), 'SHELF_OCCLUSION'
    if abs(bearing) > np.deg2rad(cfg.camera_half_fov_deg):
        return False, float('nan'), float('nan'), 'OUT_OF_VIEW'
    if distance > cfg.camera_max_range_m:
        return False, float('nan'), float('nan'), 'OUT_OF_RANGE'
    bbox_height = cfg.focal_px * cfg.marker_height_m / max(distance, 0.1)
    bbox_center = 320.0 + cfg.focal_px * np.tan(bearing)
    noisy_height = max(2.0, bbox_height + rng.normal(0.0, cfg.bbox_height_noise_px))
    noisy_center = bbox_center + rng.normal(0.0, cfg.bbox_center_noise_px)
    measured_range = cfg.focal_px * cfg.marker_height_m / noisy_height
    measured_bearing = atan2(noisy_center - 320.0, cfg.focal_px)
    return True, measured_range, measured_bearing, 'VISIBLE'


def follower_command(
    pose: np.ndarray,
    filt: ConstantVelocityFilter,
    since_detection_s: float,
    cfg: WarehouseConfig,
) -> tuple[float, float, str, float]:
    if not filt.initialized or since_detection_s > cfg.prediction_timeout_s:
        return 0.0, 0.0, 'SAFE_STOP', float('nan')
    dx, dy = filt.x[0] - pose[0], filt.x[1] - pose[1]
    distance = hypot(dx, dy)
    bearing = wrap_angle(atan2(dy, dx) - pose[2])
    state = 'TRACK' if since_detection_s <= 1.0 / cfg.camera_hz + cfg.dt_s else 'PREDICT'
    target_forward = max(0.0, filt.x[2] * cos(pose[2]) + filt.x[3] * sin(pose[2]))
    linear = target_forward * max(0.0, cos(bearing)) + 1.25 * (distance - cfg.desired_spacing_m)
    linear = float(np.clip(linear, 0.0, cfg.follower_max_speed_mps))
    if distance < 0.45:
        linear = 0.0
    angular = float(np.clip(2.35 * bearing, -cfg.max_angular_rps, cfg.max_angular_rps))
    return linear, angular, state, distance


def simulate_warehouse(seed: int = 11, follower_count: int = 3, cfg: WarehouseConfig | None = None):
    cfg = cfg or WarehouseConfig()
    rngs = [np.random.default_rng(seed + 101 * i) for i in range(follower_count)]
    robots = [np.array([2.4 - 0.8 * i, 1.2, 0.0], dtype=float) for i in range(follower_count + 1)]
    filters = [ConstantVelocityFilter() for _ in range(follower_count)]
    last_detection = [-1e9] * follower_count
    next_camera = [0.0] * follower_count
    waypoint_index = 1
    rows: list[dict[str, Any]] = []
    collision_samples = 0

    for step in range(int(cfg.duration_s / cfg.dt_s) + 1):
        t_s = step * cfg.dt_s
        commands: list[tuple[float, float]] = []
        leader_linear, leader_angular, waypoint_index = leader_command(robots[0], waypoint_index, cfg)
        commands.append((leader_linear, leader_angular))
        states = ['LEADER']
        visibility = ['PATH']
        estimated_ranges = [float('nan')]
        detections = [0]

        for follower_index in range(follower_count):
            filt = filters[follower_index]
            filt.predict(cfg.dt_s)
            robot_index = follower_index + 1
            target_index = follower_index
            detected = False
            reason = 'BETWEEN_FRAMES'
            if t_s + 1e-12 >= next_camera[follower_index]:
                detected, measured_range, measured_bearing, reason = camera_observation(
                    robots[target_index], robots[robot_index], rngs[follower_index], cfg
                )
                next_camera[follower_index] += 1.0 / cfg.camera_hz
                if detected:
                    direction = robots[robot_index][2] + measured_bearing
                    measured_world = np.array([
                        robots[robot_index][0] + measured_range * cos(direction),
                        robots[robot_index][1] + measured_range * sin(direction),
                    ])
                    filt.update(measured_world, 0.05 + 0.015 * measured_range)
                    last_detection[follower_index] = t_s
            linear, angular, state, estimated_range = follower_command(
                robots[robot_index], filt, t_s - last_detection[follower_index], cfg
            )
            commands.append((linear, angular))
            states.append(state)
            visibility.append(reason)
            estimated_ranges.append(estimated_range)
            detections.append(int(detected))

        for robot, (linear, angular) in zip(robots, commands):
            robot[0] += linear * cos(robot[2]) * cfg.dt_s
            robot[1] += linear * sin(robot[2]) * cfg.dt_s
            robot[2] = wrap_angle(robot[2] + angular * cfg.dt_s)

        shelf_collision = any(
            point_in_rect(robot[0], robot[1], rect, cfg.robot_radius_m)
            for robot in robots for rect in SHELVES
        )
        robot_collision = any(
            hypot(robots[i][0] - robots[j][0], robots[i][1] - robots[j][1]) < 2.0 * cfg.robot_radius_m
            for i in range(len(robots)) for j in range(i + 1, len(robots))
        )
        collision = shelf_collision or robot_collision
        collision_samples += int(collision)

        row: dict[str, Any] = {
            'time_s': t_s,
            'waypoint_index': waypoint_index,
            'collision': int(collision),
        }
        for index, robot in enumerate(robots):
            row[f'r{index}_x_m'] = float(robot[0])
            row[f'r{index}_y_m'] = float(robot[1])
            row[f'r{index}_yaw_rad'] = float(robot[2])
            row[f'r{index}_linear_mps'] = float(commands[index][0])
            row[f'r{index}_angular_rps'] = float(commands[index][1])
            row[f'r{index}_state'] = states[index]
            row[f'r{index}_visibility'] = visibility[index]
            row[f'r{index}_detection'] = detections[index]
            row[f'r{index}_estimated_range_m'] = estimated_ranges[index]
            if index > 0:
                row[f'r{index}_true_range_m'] = hypot(
                    robots[index - 1][0] - robot[0], robots[index - 1][1] - robot[1]
                )
        rows.append(row)

    summary = {
        'seed': seed,
        'followers': follower_count,
        'duration_s': cfg.duration_s,
        'collision_samples': collision_samples,
        'safe_stop_fraction': {
            f'follower_{index}': float(np.mean([row[f'r{index}_state'] == 'SAFE_STOP' for row in rows]))
            for index in range(1, follower_count + 1)
        },
        'spacing_rmse_m': {
            f'follower_{index}': float(np.sqrt(np.mean([
                (row[f'r{index}_true_range_m'] - cfg.desired_spacing_m) ** 2
                for row in rows if row['time_s'] >= 5.0
            ])))
            for index in range(1, follower_count + 1)
        },
        'completed_waypoints': int(rows[-1]['waypoint_index']),
        'limitations': 'kinematic model with perfect follower pose; not ROS 2 or Gazebo evidence',
    }
    return rows, summary
