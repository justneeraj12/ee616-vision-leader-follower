#!/usr/bin/env python3
"""Build a silent Gate 7 evidence walkthrough from frozen figures and facts."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = Path(__file__).resolve().parent
SLIDE_DIR = WORK_DIR / "slides"
OUTPUT = ROOT / "deliverables" / "Neeraj_Kanchani_EE616_Gate7_Evidence_Walkthrough.mp4"
WIDTH, HEIGHT = 1920, 1080
NAVY = (22, 49, 78)
BLUE = (44, 118, 180)
LIGHT = (242, 246, 250)
DARK = (25, 30, 36)
MUTED = (80, 92, 105)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)


def wrap(draw: ImageDraw.ImageDraw, text: str, selected_font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=selected_font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def base_slide(title: str, subtitle: str = "") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, HEIGHT), LIGHT)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, WIDTH, 145), fill=NAVY)
    draw.text((90, 42), title, fill="white", font=font(52, True))
    if subtitle:
        draw.text((94, 162), subtitle, fill=MUTED, font=font(28))
    draw.text((90, 1030), "EE 616-57 | Neeraj Kumar Kanchani | Simulation evidence only", fill=MUTED, font=font(21))
    return image, draw


def bullet_slide(title: str, bullets: list[str], subtitle: str = "") -> Image.Image:
    image, draw = base_slide(title, subtitle)
    y = 245
    body = font(35)
    for item in bullets:
        lines = wrap(draw, item, body, 1560)
        draw.ellipse((105, y + 13, 123, y + 31), fill=BLUE)
        for line in lines:
            draw.text((155, y), line, fill=DARK, font=body)
            y += 52
        y += 30
    return image


def figure_slide(title: str, figure: Path, caption: str) -> Image.Image:
    image, draw = base_slide(title)
    source = Image.open(figure).convert("RGB")
    source.thumbnail((1550, 620), Image.Resampling.LANCZOS)
    x = (WIDTH - source.width) // 2
    y = 170 + (620 - source.height) // 2
    draw.rounded_rectangle((x - 8, y - 8, x + source.width + 8, y + source.height + 8), radius=12, fill="white", outline=(190, 200, 210), width=2)
    image.paste(source, (x, y))
    caption_font = font(25)
    lines = wrap(draw, caption, caption_font, 1650)
    caption_y = 850
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=caption_font)
        draw.text(((WIDTH - (bbox[2] - bbox[0])) / 2, caption_y), line, fill=MUTED, font=caption_font)
        caption_y += 31
    return image


def title_slide() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), NAVY)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 850, WIDTH, HEIGHT), fill=BLUE)
    draw.text((115, 235), "Vision-Based Predecessor-Following", fill="white", font=font(66, True))
    draw.text((115, 330), "Warehouse Convoys", fill="white", font=font(82, True))
    draw.text((120, 475), "Gate 7 frozen evidence walkthrough", fill=(205, 224, 241), font=font(42))
    draw.text((120, 895), "Neeraj Kumar Kanchani | EE 616-57 | Professor Masudul Imtiaz", fill="white", font=font(31))
    return image


def build_slides() -> list[Image.Image]:
    results = ROOT / "work" / "ros2_ws" / "results"
    return [
        title_slide(),
        bullet_slide("Implemented system", [
            "One deterministic route-owning leader and up to three independently driven followers.",
            "Each follower uses a forward RGB camera, local wheel odometry, YOLOv8n, a relative-state EKF, bounded control, and TRACK / PREDICT / SAFE STOP.",
            "Gazebo pose truth is restricted to evaluation and never enters perception or control.",
        ]),
        figure_slide(
            "Gate 2: sealed camera measurement",
            results / "yolo_measurement_gate_v3" / "camera_measurement_errors.png",
            "YOLOv8n v3: 100% valid full-visible measurements, 0.0323 m range RMSE, 0.1569 degree bearing MAE, and 9.02 ms p95 inference latency.",
        ),
        figure_slide(
            "Gate 3: validated leader-follower pair",
            results / "pair_gate" / "pair_gate_metrics.png",
            "Six nominal runs passed. Worst spacing RMSE was 0.0558 m straight and 0.1005 m during gradual turns.",
        ),
        figure_slide(
            "Gate 4: incremental chain",
            results / "chain_gate" / "chain_gate_metrics.png",
            "Two followers passed before three followers were launched. Nominal rearward amplification was not observed.",
        ),
        figure_slide(
            "Gate 5: controlled disturbances",
            results / "disturbance_gate" / "disturbance_gate_metrics.png",
            "All 18 pair-first runs passed. The combined chain showed rearward RMSE growth and required visual-loss recovery behavior.",
        ),
        figure_slide(
            "Gate 6: target-laptop timing",
            results / "timing_gate" / "timing_gate_metrics.png",
            "All three runs passed. Minimum RTF was 0.9996; peak RAM was 3,584 MiB and peak visible VRAM was 642 MiB.",
        ),
        bullet_slide("Evidence boundary", [
            "These results demonstrate the declared ROS 2 and Gazebo simulation configuration on one laptop.",
            "The visual blackout is synthetic, and the command bias is not physical wheel slip.",
            "The project does not demonstrate physical robots, person safety, certification, or production readiness.",
            "The Gate 7 archive preserves source, protocols, successful evidence, failed detector attempts, checksums, and the technical handbook.",
        ]),
    ]


def main() -> int:
    SLIDE_DIR.mkdir(parents=True, exist_ok=True)
    slides = build_slides()
    paths = []
    for index, image in enumerate(slides, 1):
        path = SLIDE_DIR / f"slide_{index:02d}.png"
        image.save(path)
        paths.append(path)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fps = 30.0
    writer = cv2.VideoWriter(
        str(OUTPUT), cv2.VideoWriter_fourcc(*"mp4v"), fps, (WIDTH, HEIGHT)
    )
    if not writer.isOpened():
        raise RuntimeError("OpenCV could not initialize the MP4 video writer")
    frames_per_slide = int(5.0 * fps)
    try:
        for image in slides:
            frame = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
            for _ in range(frames_per_slide):
                writer.write(frame)
    finally:
        writer.release()
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
