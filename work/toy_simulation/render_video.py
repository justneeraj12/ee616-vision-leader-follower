from __future__ import annotations

import csv
import math
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'work' / 'toy_simulation' / 'results' / 'representative_occlusion_timeseries.csv'
OUTPUT = ROOT / 'deliverables' / 'Neeraj_Kanchani_EE616_Toy_Simulation_2D.mp4'

WIDTH, HEIGHT = 1920, 1080
FPS = 30
DURATION_S = 20.0
MAP = (70, 150, 1390, 930)
PANEL = (1440, 150, 1850, 930)

NAVY = '#0B3557'
BLUE = '#2474A6'
GREEN = '#2E7D5B'
ORANGE = '#D97706'
RED = '#B23A48'
INK = '#162733'
MUTED = '#627789'
GRID = '#D8E2EA'
PALE = '#F4F8FB'
WHITE = '#FFFFFF'


def font(size: int, bold: bool = False):
    filename = 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    return ImageFont.truetype(f'/usr/share/fonts/truetype/dejavu/{filename}', size)


def load_rows() -> list[dict]:
    rows = []
    with DATA.open(newline='', encoding='utf-8') as stream:
        for row in csv.DictReader(stream):
            numeric = {}
            for key, value in row.items():
                if key in {'scenario', 'control_state'}:
                    numeric[key] = value
                else:
                    try:
                        numeric[key] = float(value)
                    except ValueError:
                        numeric[key] = float('nan')
            rows.append(numeric)
    return rows


def world_mapper(rows: list[dict]):
    xs = [r['leader_x_m'] for r in rows] + [r['follower_x_m'] for r in rows]
    ys = [r['leader_y_m'] for r in rows] + [r['follower_y_m'] for r in rows]
    x_min, x_max = min(xs) - 0.8, max(xs) + 0.8
    y_mid = 0.5 * (min(ys) + max(ys))
    x_span = x_max - x_min
    map_w = MAP[2] - MAP[0]
    map_h = MAP[3] - MAP[1]
    y_span = x_span * map_h / map_w
    y_min, y_max = y_mid - y_span / 2, y_mid + y_span / 2

    def project(x: float, y: float) -> tuple[float, float]:
        px = MAP[0] + (x - x_min) / (x_max - x_min) * map_w
        py = MAP[3] - (y - y_min) / (y_max - y_min) * map_h
        return px, py

    return project, (x_min, x_max, y_min, y_max)


def interp_row(rows: list[dict], t_s: float) -> tuple[dict, int]:
    index = min(len(rows) - 2, max(0, int(t_s / 0.02)))
    a, b = rows[index], rows[index + 1]
    alpha = (t_s - a['time_s']) / max(1e-9, b['time_s'] - a['time_s'])
    out = dict(a)
    for key in a:
        if key in {'scenario', 'control_state'}:
            continue
        if math.isfinite(a[key]) and math.isfinite(b[key]):
            out[key] = a[key] + alpha * (b[key] - a[key])
    out['control_state'] = a['control_state']
    return out, index


def draw_robot(draw: ImageDraw.ImageDraw, x: float, y: float, yaw: float, color: str, label: str) -> None:
    radius = 20
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=WHITE, outline=color, width=7)
    tip = (x + 31 * math.cos(yaw), y - 31 * math.sin(yaw))
    left = (x + 12 * math.cos(yaw + 2.45), y - 12 * math.sin(yaw + 2.45))
    right = (x + 12 * math.cos(yaw - 2.45), y - 12 * math.sin(yaw - 2.45))
    draw.polygon((tip, left, right), fill=color)
    draw.text((x - 52, y + 30), label, fill=color, font=font(20, True))


def draw_panel(draw: ImageDraw.ImageDraw, row: dict, t_s: float) -> None:
    x1, y1, x2, y2 = PANEL
    draw.rounded_rectangle(PANEL, radius=20, fill=PALE, outline=GRID, width=3)
    draw.text((x1 + 28, y1 + 28), 'LIVE TELEMETRY', fill=NAVY, font=font(25, True))
    draw.text((x1 + 28, y1 + 78), f'{t_s:05.2f} s', fill=INK, font=font(46, True))
    state = row['control_state']
    state_color = {'TRACK': GREEN, 'PREDICT': ORANGE, 'SAFE_STOP': RED}[state]
    draw.rounded_rectangle((x1 + 28, y1 + 145, x2 - 28, y1 + 205), radius=14, fill=state_color)
    box = draw.textbbox((0, 0), state, font=font(25, True))
    draw.text(((x1 + x2 - (box[2] - box[0])) / 2, y1 + 160), state, fill=WHITE, font=font(25, True))

    estimated = row['estimated_range_m']
    error = estimated - row['true_range_m'] if math.isfinite(estimated) else float('nan')
    values = [
        ('True range', f"{row['true_range_m']:.3f} m"),
        ('Filtered range', f'{estimated:.3f} m' if math.isfinite(estimated) else 'initializing'),
        ('Range error', f'{error:+.3f} m' if math.isfinite(error) else '--'),
        ('True bearing', f"{math.degrees(row['true_bearing_rad']):+.2f} deg"),
        ('Linear command', f"{row['linear_cmd_mps']:.3f} m/s"),
        ('Angular command', f"{row['angular_cmd_rps']:+.3f} rad/s"),
    ]
    y = y1 + 245
    for label, value in values:
        draw.text((x1 + 28, y), label, fill=MUTED, font=font(19))
        draw.text((x2 - 28, y), value, fill=INK, font=font(21, True), anchor='ra')
        draw.line((x1 + 28, y + 36, x2 - 28, y + 36), fill=GRID, width=2)
        y += 66

    camera_available = bool(row['detection'])
    draw.ellipse((x1 + 28, y + 12, x1 + 48, y + 32), fill=GREEN if camera_available else MUTED)
    draw.text((x1 + 62, y + 7), 'new camera measurement' if camera_available else 'prediction between frames', fill=INK, font=font(18))

    y += 74
    phase = 'FORCED OCCLUSION' if 8.0 <= t_s < 9.17 else 'NOMINAL VISIBILITY'
    phase_color = RED if phase.startswith('FORCED') else GREEN
    draw.text((x1 + 28, y), 'SCENARIO PHASE', fill=MUTED, font=font(17, True))
    draw.text((x1 + 28, y + 31), phase, fill=phase_color, font=font(20, True))
    draw.text((x1 + 28, y + 82), 'Toy kinematic baseline', fill=NAVY, font=font(18, True))
    draw.text((x1 + 28, y + 112), 'Not ROS 2 or Gazebo evidence', fill=RED, font=font(17))


def render_frame(rows: list[dict], project, bounds, t_s: float) -> Image.Image:
    row, index = interp_row(rows, t_s)
    image = Image.new('RGB', (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)
    draw.text((70, 42), 'Vision Only Leader Follower Toy Simulation', fill=NAVY, font=font(39, True))
    draw.text((72, 94), 'Representative S-curve trial with a forced camera occlusion', fill=MUTED, font=font(23))

    draw.rounded_rectangle(MAP, radius=18, fill=PALE, outline=GRID, width=3)
    x_min, x_max, y_min, y_max = bounds
    for i in range(math.floor(x_min), math.ceil(x_max) + 1):
        x, _ = project(i, 0)
        draw.line((x, MAP[1], x, MAP[3]), fill=GRID, width=1)
        draw.text((x + 5, MAP[3] - 28), f'{i} m', fill=MUTED, font=font(15))
    for j in np.arange(math.floor(y_min), math.ceil(y_max) + 0.5, 0.5):
        _, y = project(0, float(j))
        draw.line((MAP[0], y, MAP[2], y), fill=GRID, width=1)

    leader_path = [project(r['leader_x_m'], r['leader_y_m']) for r in rows[: index + 1]]
    follower_path = [project(r['follower_x_m'], r['follower_y_m']) for r in rows[: index + 1]]
    if len(leader_path) > 1:
        draw.line(leader_path, fill=NAVY, width=5)
        draw.line(follower_path, fill=BLUE, width=5)

    fx, fy = project(row['follower_x_m'], row['follower_y_m'])
    lx, ly = project(row['leader_x_m'], row['leader_y_m'])
    scale = (MAP[2] - MAP[0]) / (x_max - x_min)
    cone_length = min(4.0 * scale, 340)
    half = math.radians(42.0)
    yaw = row['follower_yaw_rad']
    overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    cone = [
        (fx, fy),
        (fx + cone_length * math.cos(yaw + half), fy - cone_length * math.sin(yaw + half)),
        (fx + cone_length * math.cos(yaw - half), fy - cone_length * math.sin(yaw - half)),
    ]
    cone_fill = (217, 119, 6, 38) if 8.0 <= t_s < 9.17 else (36, 116, 166, 30)
    odraw.polygon(cone, fill=cone_fill)
    image = Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(image)

    desired_radius = 1.5 * scale
    draw.ellipse((fx - desired_radius, fy - desired_radius, fx + desired_radius, fy + desired_radius), outline='#9FB3C3', width=3)
    draw.line((fx, fy, lx, ly), fill=ORANGE if 8.0 <= t_s < 9.17 else GREEN, width=3)
    draw_robot(draw, lx, ly, math.atan2(row['leader_vy_mps'], row['leader_vx_mps']), NAVY, 'LEADER')
    draw_robot(draw, fx, fy, yaw, BLUE, 'FOLLOWER')

    draw_panel(draw, row, t_s)

    timeline_y = 1005
    draw.line((70, timeline_y, 1850, timeline_y), fill=GRID, width=12)
    occ_x1 = 70 + 8.0 / DURATION_S * 1780
    occ_x2 = 70 + 9.17 / DURATION_S * 1780
    draw.line((occ_x1, timeline_y, occ_x2, timeline_y), fill=RED, width=12)
    current_x = 70 + t_s / DURATION_S * 1780
    draw.ellipse((current_x - 12, timeline_y - 12, current_x + 12, timeline_y + 12), fill=NAVY)
    draw.text((70, 1025), '0 s', fill=MUTED, font=font(16))
    draw.text((1830, 1025), '20 s', fill=MUTED, font=font(16))
    draw.text(((occ_x1 + occ_x2) / 2, 1025), 'forced occlusion', fill=RED, font=font(16, True), anchor='ma')
    return image


def main() -> None:
    rows = load_rows()
    project, bounds = world_mapper(rows)
    if shutil.which('ffmpeg'):
        command = [
            'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo', '-pix_fmt', 'rgb24',
            '-s', f'{WIDTH}x{HEIGHT}', '-r', str(FPS), '-i', '-', '-an', '-c:v', 'libx264',
            '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(OUTPUT),
        ]
    else:
        OUTPUT.unlink(missing_ok=True)
        command = [
            'gst-launch-1.0', '-q', 'fdsrc', 'fd=0', '!', 'rawvideoparse', 'format=rgb',
            f'width={WIDTH}', f'height={HEIGHT}', f'framerate={FPS}/1', '!', 'videoconvert', '!',
            'video/x-raw,format=I420', '!',
            'x264enc', 'speed-preset=medium', 'bitrate=8000', 'key-int-max=60', '!',
            'video/x-h264,stream-format=avc,alignment=au', '!', 'mp4mux', 'faststart=true', '!',
            'filesink', f'location={OUTPUT}',
        ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    for frame_index in range(int(DURATION_S * FPS)):
        t_s = frame_index / FPS
        frame = render_frame(rows, project, bounds, t_s)
        process.stdin.write(frame.tobytes())
    process.stdin.close()
    return_code = process.wait()
    if return_code != 0:
        raise SystemExit(return_code)
    print(OUTPUT)


if __name__ == '__main__':
    main()
