from __future__ import annotations

from math import isfinite
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


NAVY = "#0B3557"
BLUE = "#2474A6"
ORANGE = "#D97706"
GREEN = "#2E7D5B"
RED = "#B23A48"
GRID = "#D9E2EA"
TEXT = "#1E2933"
PALE = "#F5F8FA"


def _font(size: int, bold: bool = False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)


def _base(title: str, subtitle: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (1600, 900), "white")
    draw = ImageDraw.Draw(image)
    draw.text((80, 48), title, fill=NAVY, font=_font(38, True))
    draw.text((82, 102), subtitle, fill=TEXT, font=_font(21))
    return image, draw


def _axes(draw, box, x_min, x_max, y_min, y_max, x_label, y_label):
    left, top, right, bottom = box
    draw.rectangle(box, fill=PALE, outline=GRID, width=2)
    for i in range(6):
        x = left + (right - left) * i / 5
        y = top + (bottom - top) * i / 5
        draw.line((x, top, x, bottom), fill=GRID, width=1)
        draw.line((left, y, right, y), fill=GRID, width=1)
        xv = x_min + (x_max - x_min) * i / 5
        yv = y_max - (y_max - y_min) * i / 5
        draw.text((x - 18, bottom + 10), f"{xv:.1f}", fill=TEXT, font=_font(16))
        draw.text((left - 62, y - 10), f"{yv:.2f}", fill=TEXT, font=_font(16))
    draw.text(((left + right) / 2 - 70, bottom + 48), x_label, fill=TEXT, font=_font(19, True))
    draw.text((left - 70, top - 34), y_label, fill=TEXT, font=_font(19, True))


def _map_points(xs, ys, box, x_min, x_max, y_min, y_max):
    left, top, right, bottom = box
    points = []
    for x, y in zip(xs, ys):
        if not isfinite(float(x)) or not isfinite(float(y)):
            continue
        px = left + (float(x) - x_min) / max(1e-9, x_max - x_min) * (right - left)
        py = bottom - (float(y) - y_min) / max(1e-9, y_max - y_min) * (bottom - top)
        points.append((px, py))
    return points


def _line(draw, xs, ys, box, bounds, color, width=4):
    points = _map_points(xs, ys, box, *bounds)
    if len(points) >= 2:
        draw.line(points, fill=color, width=width)


def save_range_figure(rows: list[dict], path: Path) -> None:
    image, draw = _base("Monocular Range Baseline", "Camera-like bounding-box geometry during the representative occlusion trial")
    box = (140, 180, 1510, 750)
    times = [r["time_s"] for r in rows]
    true_ranges = [r["true_range_m"] for r in rows]
    measured = [r["measured_range_m"] for r in rows]
    estimated = [r["estimated_range_m"] for r in rows]
    y_min, y_max = 0.8, max(true_ranges) + 0.35
    bounds = (0.0, max(times), y_min, y_max)
    _axes(draw, box, *bounds, "Time s", "Range m")
    _line(draw, times, true_ranges, box, bounds, NAVY, 5)
    _line(draw, times, estimated, box, bounds, GREEN, 4)
    detected_t = [r["time_s"] for r in rows if r["detection"]]
    detected_r = [r["measured_range_m"] for r in rows if r["detection"]]
    for point in _map_points(detected_t, detected_r, box, *bounds)[::2]:
        draw.ellipse((point[0] - 2, point[1] - 2, point[0] + 2, point[1] + 2), fill=ORANGE)
    x1 = box[0] + 8.0 / max(times) * (box[2] - box[0])
    x2 = box[0] + 9.17 / max(times) * (box[2] - box[0])
    draw.rectangle((x1, box[1], x2, box[3]), outline=RED, width=3)
    draw.text((x1 + 10, box[1] + 12), "forced occlusion", fill=RED, font=_font(18, True))
    draw.text((1080, 120), "True", fill=NAVY, font=_font(18, True))
    draw.text((1180, 120), "Measured", fill=ORANGE, font=_font(18, True))
    draw.text((1330, 120), "Filtered", fill=GREEN, font=_font(18, True))
    image.save(path)


def save_trajectory_figure(rows: list[dict], path: Path) -> None:
    image, draw = _base("Closed Loop Formation Tracking", "Representative S-curve trial with a 1.50 m desired following distance")
    box = (140, 180, 1510, 750)
    lx = [r["leader_x_m"] for r in rows]
    ly = [r["leader_y_m"] for r in rows]
    fx = [r["follower_x_m"] for r in rows]
    fy = [r["follower_y_m"] for r in rows]
    x_min, x_max = min(fx + lx) - 0.3, max(fx + lx) + 0.3
    y_min, y_max = min(fy + ly) - 0.4, max(fy + ly) + 0.4
    bounds = (x_min, x_max, y_min, y_max)
    _axes(draw, box, *bounds, "World x m", "World y m")
    _line(draw, lx, ly, box, bounds, NAVY, 6)
    _line(draw, fx, fy, box, bounds, BLUE, 5)
    draw.text((1120, 120), "Leader path", fill=NAVY, font=_font(18, True))
    draw.text((1300, 120), "Follower path", fill=BLUE, font=_font(18, True))
    image.save(path)


def save_occlusion_figure(rows: list[dict], path: Path) -> None:
    image, draw = _base("Occlusion State Transition", "The estimator predicts through the forced dropout and returns to tracking on the first new camera frame")
    box = (140, 210, 1510, 700)
    times = [r["time_s"] for r in rows]
    ranges = [r["true_range_m"] for r in rows]
    bounds = (6.5, 10.8, min(ranges) - 0.15, max(ranges) + 0.15)
    _axes(draw, box, *bounds, "Time s", "True range m")
    colors = {"TRACK": GREEN, "PREDICT": ORANGE, "SAFE_STOP": RED}
    for row in rows:
        if not 6.5 <= row["time_s"] <= 10.8:
            continue
        points = _map_points([row["time_s"]], [row["true_range_m"]], box, *bounds)
        if points:
            x, y = points[0]
            draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=colors[row["control_state"]])
    for i, state in enumerate(["TRACK", "PREDICT", "SAFE_STOP"]):
        draw.text((1030 + i * 155, 140), state, fill=colors[state], font=_font(18, True))
    image.save(path)


def save_summary_figure(summary: dict, path: Path) -> None:
    image, draw = _base("Toy Baseline Summary", "Median results across deterministic trials; thresholds are project targets, not validated system claims")
    cards = [
        ("Range RMSE", summary["overall_median"]["range_rmse_m"], 0.20, "m"),
        ("Bearing MAE", summary["overall_median"]["bearing_mae_deg"], 5.00, "deg"),
        ("Formation RMSE", summary["overall_median"]["formation_rmse_m"], 0.25, "m"),
        ("Reacquisition", summary["occlusion_median_reacquisition_s"], 3.00, "s"),
    ]
    for i, (label, value, target, unit) in enumerate(cards):
        x = 90 + i * 375
        draw.rounded_rectangle((x, 200, x + 330, 520), radius=18, fill=PALE, outline=GRID, width=3)
        draw.text((x + 28, 235), label, fill=NAVY, font=_font(24, True))
        draw.text((x + 28, 315), f"{value:.3f} {unit}", fill=GREEN if value <= target else RED, font=_font(38, True))
        draw.text((x + 28, 390), f"proposed target <= {target:.2f} {unit}", fill=TEXT, font=_font(18))
        draw.text((x + 28, 452), "TOY MODEL ONLY", fill=ORANGE, font=_font(17, True))
    draw.text((92, 610), f"Trials: {summary['trial_count']}  |  Collision samples: {summary['collision_samples_total']}  |  Seeds are recorded in trial_metrics.csv", fill=TEXT, font=_font(24, True))
    draw.text((92, 680), "Next gate: reproduce the measurement experiment in Gazebo before detector, EKF, or controller claims are accepted.", fill=NAVY, font=_font(22))
    image.save(path)
