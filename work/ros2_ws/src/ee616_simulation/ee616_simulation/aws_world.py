"""Prepare the pinned AWS no-roof world for an EE 616 resource benchmark."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def _add_camera_and_target(world: ET.Element) -> None:
    camera_model = ET.SubElement(world, "model", {"name": "ee616_benchmark_camera"})
    ET.SubElement(camera_model, "static").text = "true"
    ET.SubElement(camera_model, "pose").text = "-8 0 0.65 0 0 0"
    camera_link = ET.SubElement(camera_model, "link", {"name": "camera_link"})
    sensor = ET.SubElement(camera_link, "sensor", {"name": "front_camera", "type": "camera"})
    ET.SubElement(sensor, "topic").text = "/smoke/camera/image"
    ET.SubElement(sensor, "update_rate").text = "15"
    ET.SubElement(sensor, "always_on").text = "true"
    ET.SubElement(sensor, "visualize").text = "true"
    camera = ET.SubElement(sensor, "camera")
    ET.SubElement(camera, "horizontal_fov").text = "1.2217304764"
    image = ET.SubElement(camera, "image")
    ET.SubElement(image, "width").text = "640"
    ET.SubElement(image, "height").text = "480"
    ET.SubElement(image, "format").text = "R8G8B8"
    clip = ET.SubElement(camera, "clip")
    ET.SubElement(clip, "near").text = "0.1"
    ET.SubElement(clip, "far").text = "30"

    target_model = ET.SubElement(world, "model", {"name": "ee616_visual_target"})
    ET.SubElement(target_model, "static").text = "true"
    ET.SubElement(target_model, "pose").text = "-5 0 0.6 0 0 0"
    target_link = ET.SubElement(target_model, "link", {"name": "target_link"})
    for element_name in ("collision", "visual"):
        element = ET.SubElement(target_link, element_name, {"name": element_name})
        box = ET.SubElement(ET.SubElement(element, "geometry"), "box")
        ET.SubElement(box, "size").text = "0.08 0.7 0.9"
        if element_name == "visual":
            material = ET.SubElement(element, "material")
            ET.SubElement(material, "ambient").text = "0.9 0.15 0.05 1"
            ET.SubElement(material, "diffuse").text = "0.9 0.15 0.05 1"


def prepare_aws_world(source: Path, output_dir: Path) -> dict[str, Any]:
    """Copy the vendor world and append only benchmark camera assets."""
    source_bytes = source.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    tree = ET.parse(source)
    root = tree.getroot()
    world = root.find("world")
    if world is None:
        raise ValueError("AWS source world has no world element.")
    world.set("name", "aws_no_roof_warehouse")
    if world.find("model[@name='ee616_benchmark_camera']") is not None:
        raise ValueError("AWS source world already contains EE 616 benchmark assets.")
    _add_camera_and_target(world)
    ET.indent(tree, space="  ")

    output_dir.mkdir(parents=True, exist_ok=True)
    world_path = output_dir / f"aws-no-roof-{source_hash[:12]}.sdf"
    manifest_path = output_dir / f"aws-no-roof-{source_hash[:12]}.json"
    tree.write(world_path, encoding="unicode", xml_declaration=True)
    manifest = {
        "scenario": "aws_no_roof_warehouse",
        "source_world": str(source),
        "source_sha256": source_hash,
        "world_path": str(world_path),
        "adaptations": [
            "renamed world for isolated Gazebo topics",
            "added fixed 640x480 15 Hz RGB camera",
            "added static red visual target",
        ],
        "scope": "optional visual and resource stress test; not control evidence",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest
