from __future__ import annotations

import csv
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from toy_swarm.warehouse import SHELVES, WAYPOINTS


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'work' / 'toy_simulation' / 'warehouse_results' / 'warehouse_multi_timeseries.csv'
OUTPUT = ROOT / 'deliverables' / 'Neeraj_Kanchani_EE616_Multi_Follower_Warehouse_2D.mp4'

WIDTH, HEIGHT = 1920, 1080
FPS = 24
PLAYBACK_SPEED = 2.0
SIM_DURATION = 86.0
VIDEO_DURATION = SIM_DURATION / PLAYBACK_SPEED
MAP = (55, 135, 1465, 960)
PANEL = (1505, 135, 1870, 960)

NAVY = '#0B3557'
BLUE = '#2474A6'
GREEN = '#2E7D5B'
PURPLE = '#7A4FA3'
ORANGE = '#D97706'
RED = '#B23A48'
INK = '#182832'
MUTED = '#667A8B'
GRID = '#D8E2EA'
PALE = '#F4F8FB'
WHITE = '#FFFFFF'
SHELF = '#5D6973'
ROBOT_COLORS = (NAVY, BLUE, GREEN, PURPLE)


def font(size: int, bold: bool = False):
    name = 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    return ImageFont.truetype(f'/usr/share/fonts/truetype/dejavu/{name}', size)


def load_rows() -> list[dict]:
    rows = []
    with DATA.open(newline='', encoding='utf-8') as stream:
        for source in csv.DictReader(stream):
            row = {}
            for key, value in source.items():
                if key.endswith('_state') or key.endswith('_visibility'):
                    row[key] = value
                else:
                    try:
                        row[key] = float(value)
                    except ValueError:
                        row[key] = value
            rows.append(row)
    return rows


def interp(rows: list[dict], sim_t: float):
    index = min(len(rows) - 2, max(0, int(sim_t / 0.02)))
    a, b = rows[index], rows[index + 1]
    alpha = (sim_t - a['time_s']) / max(1e-9, b['time_s'] - a['time_s'])
    row = dict(a)
    for key, value in a.items():
        if isinstance(value, float) and isinstance(b[key], float) and math.isfinite(value) and math.isfinite(b[key]):
            row[key] = value + alpha * (b[key] - value)
    return row, index


def project(x: float, y: float) -> tuple[float, float]:
    px = MAP[0] + x / 16.0 * (MAP[2] - MAP[0])
    py = MAP[3] - y / 10.2 * (MAP[3] - MAP[1])
    return px, py


def draw_robot(draw, x, y, yaw, color, label):
    radius = 16
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=WHITE, outline=color, width=6)
    tip = (x + 27 * math.cos(yaw), y - 27 * math.sin(yaw))
    left = (x + 10 * math.cos(yaw + 2.4), y - 10 * math.sin(yaw + 2.4))
    right = (x + 10 * math.cos(yaw - 2.4), y - 10 * math.sin(yaw - 2.4))
    draw.polygon((tip, left, right), fill=color)
    draw.text((x, y + 24), label, fill=color, font=font(16, True), anchor='ma')


def camera_cone(overlay, x, y, yaw, color):
    half = math.radians(58)
    length = 185
    points = [
        (x, y),
        (x + length * math.cos(yaw + half), y - length * math.sin(yaw + half)),
        (x + length * math.cos(yaw - half), y - length * math.sin(yaw - half)),
    ]
    rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
    ImageDraw.Draw(overlay).polygon(points, fill=(*rgb, 24))


def draw_panel(draw, row, sim_t):
    x1, y1, x2, y2 = PANEL
    draw.rounded_rectangle(PANEL, radius=18, fill=PALE, outline=GRID, width=3)
    draw.text((x1 + 22, y1 + 24), 'MULTI ROBOT STATUS', fill=NAVY, font=font(23, True))
    draw.text((x1 + 22, y1 + 63), f'Simulation {sim_t:05.1f} s', fill=INK, font=font(29, True))
    draw.text((x1 + 22, y1 + 105), f'Playback {PLAYBACK_SPEED:.0f}x', fill=MUTED, font=font(18))

    y = y1 + 155
    names = ('Leader', 'Follower 1', 'Follower 2', 'Follower 3')
    for i, name in enumerate(names):
        color = ROBOT_COLORS[i]
        draw.line((x1 + 22, y, x1 + 52, y), fill=color, width=8)
        draw.text((x1 + 66, y - 14), name, fill=color, font=font(20, True))
        if i == 0:
            draw.text((x2 - 22, y - 14), 'WAYPOINT NAV', fill=INK, font=font(16, True), anchor='ra')
            draw.text((x1 + 22, y + 24), f"Speed {row['r0_linear_mps']:.2f} m/s", fill=MUTED, font=font(16))
        else:
            state = row[f'r{i}_state']
            state_color = {'TRACK': GREEN, 'PREDICT': ORANGE, 'SAFE_STOP': RED}[state]
            draw.text((x2 - 22, y - 14), state, fill=state_color, font=font(17, True), anchor='ra')
            draw.text((x1 + 22, y + 24), f"Spacing {row[f'r{i}_true_range_m']:.2f} m", fill=INK, font=font(16))
            visibility = row[f'r{i}_visibility'].replace('_', ' ').title()
            draw.text((x2 - 22, y + 24), visibility, fill=MUTED, font=font(15), anchor='ra')
        draw.line((x1 + 22, y + 58, x2 - 22, y + 58), fill=GRID, width=2)
        y += 100

    draw.text((x1 + 22, y + 3), 'EXPERIMENT', fill=MUTED, font=font(16, True))
    draw.text((x1 + 22, y + 34), '3 independent followers', fill=INK, font=font(18, True))
    draw.text((x1 + 22, y + 65), 'Each tracks the robot ahead', fill=INK, font=font(16))
    draw.text((x1 + 22, y + 96), 'Camera-like range and bearing', fill=INK, font=font(16))
    draw.text((x1 + 22, y + 127), 'No centralized follower control', fill=INK, font=font(16))
    draw.text((x1 + 22, y + 174), 'Toy model only', fill=ORANGE, font=font(18, True))
    draw.text((x1 + 22, y + 204), 'Next validation gate is Gazebo', fill=RED, font=font(16))


def render(rows, video_t):
    sim_t = min(SIM_DURATION, video_t * PLAYBACK_SPEED)
    row, index = interp(rows, sim_t)
    image = Image.new('RGB', (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)
    draw.text((55, 35), 'Multi Follower Coordination in a Warehouse Maze', fill=NAVY, font=font(38, True))
    draw.text((57, 84), 'Leader plus three independently controlled vision followers', fill=MUTED, font=font(22))
    draw.rounded_rectangle(MAP, radius=16, fill=PALE, outline=GRID, width=3)

    for x in range(17):
        px, _ = project(x, 0)
        draw.line((px, MAP[1], px, MAP[3]), fill=GRID, width=1)
    for y in range(11):
        _, py = project(0, y)
        draw.line((MAP[0], py, MAP[2], py), fill=GRID, width=1)

    for shelf_index, (x1, y1, x2, y2) in enumerate(SHELVES, 1):
        left, bottom = project(x1, y1)
        right, top = project(x2, y2)
        draw.rounded_rectangle((left, top, right, bottom), radius=7, fill=SHELF, outline=INK, width=2)
        draw.text(((left + right) / 2, (top + bottom) / 2), f'SHELF {shelf_index}', fill=WHITE, font=font(17, True), anchor='mm')

    path_points = [project(x, y) for x, y in WAYPOINTS]
    draw.line(path_points, fill='#9EB0BE', width=3)
    for p in path_points:
        draw.ellipse((p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5), fill='#9EB0BE')

    for robot_index, color in enumerate(ROBOT_COLORS):
        trail = [project(r[f'r{robot_index}_x_m'], r[f'r{robot_index}_y_m']) for r in rows[:index + 1:4]]
        if len(trail) > 1:
            draw.line(trail, fill=color, width=4)

    overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    for robot_index in range(1, 4):
        x, y = project(row[f'r{robot_index}_x_m'], row[f'r{robot_index}_y_m'])
        camera_cone(overlay, x, y, row[f'r{robot_index}_yaw_rad'], ROBOT_COLORS[robot_index])
    image = Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(image)

    for robot_index in range(3, -1, -1):
        x, y = project(row[f'r{robot_index}_x_m'], row[f'r{robot_index}_y_m'])
        label = 'L' if robot_index == 0 else f'F{robot_index}'
        draw_robot(draw, x, y, row[f'r{robot_index}_yaw_rad'], ROBOT_COLORS[robot_index], label)

    draw_panel(draw, row, sim_t)
    progress_y = 1015
    draw.line((55, progress_y, 1870, progress_y), fill=GRID, width=12)
    current_x = 55 + video_t / VIDEO_DURATION * 1815
    draw.ellipse((current_x - 12, progress_y - 12, current_x + 12, progress_y + 12), fill=NAVY)
    draw.text((55, 1035), 'Start', fill=MUTED, font=font(16))
    draw.text((1870, 1035), 'Finish', fill=MUTED, font=font(16), anchor='ra')
    return image


def main():
    rows = load_rows()
    OUTPUT.unlink(missing_ok=True)
    command = [
        'gst-launch-1.0', '-q', 'fdsrc', 'fd=0', '!', 'rawvideoparse', 'format=rgb',
        f'width={WIDTH}', f'height={HEIGHT}', f'framerate={FPS}/1', '!', 'videoconvert', '!',
        'video/x-raw,format=I420', '!', 'x264enc', 'speed-preset=medium', 'bitrate=8000',
        'key-int-max=48', '!', 'video/x-h264,stream-format=avc,alignment=au', '!',
        'mp4mux', 'faststart=true', '!', 'filesink', f'location={OUTPUT}',
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    for frame_index in range(int(VIDEO_DURATION * FPS)):
        frame = render(rows, frame_index / FPS)
        process.stdin.write(frame.tobytes())
    process.stdin.close()
    code = process.wait()
    if code:
        raise SystemExit(code)
    print(OUTPUT)


if __name__ == '__main__':
    main()
