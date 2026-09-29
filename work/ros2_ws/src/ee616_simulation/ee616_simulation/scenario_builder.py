"""Build deterministic Gazebo camera-measurement worlds from YAML scenarios."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml


SCENARIO_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
VECTOR_LENGTHS = {
    "pose": 6,
    "size": 3,
    "color": 4,
}


class ScenarioError(ValueError):
    """Raised when a scenario file is unsafe or incomplete."""


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ScenarioError(f"Unable to read scenario {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ScenarioError(f"Scenario {path} must contain a YAML mapping.")
    return data


def load_scenario(path: Path) -> tuple[dict[str, Any], list[Path]]:
    """Load one scenario and its optional single-file base template."""
    path = path.resolve()
    data = _read_yaml(path)
    sources = [path]
    base_name = data.pop("extends", None)
    if base_name is not None:
        if not isinstance(base_name, str) or Path(base_name).name != base_name:
            raise ScenarioError("extends must name a YAML file in the scenario directory.")
        base_path = (path.parent / base_name).resolve()
        if base_path.parent != path.parent or base_path == path:
            raise ScenarioError("Scenario inheritance must remain in one directory.")
        base = _read_yaml(base_path)
        if "extends" in base:
            raise ScenarioError("Only one inheritance level is supported.")
        data = _deep_merge(base, data)
        sources.insert(0, base_path)
    validate_scenario(data)
    return data, sources


def _numeric_vector(value: Any, length: int, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        raise ScenarioError(f"{label} must contain exactly {length} numbers.")
    if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value):
        raise ScenarioError(f"{label} must contain only numbers.")
    return [float(item) for item in value]


def validate_scenario(data: dict[str, Any]) -> None:
    """Validate the bounded schema used by the project scenario generator."""
    if data.get("schema_version") != 1:
        raise ScenarioError("schema_version must be 1.")
    name = data.get("name")
    if not isinstance(name, str) or not SCENARIO_NAME.fullmatch(name):
        raise ScenarioError("name must use lowercase letters, numbers, and underscores.")
    for field in ("description", "variable_under_test", "expected_visibility", "evidence_scope"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ScenarioError(f"{field} must be a non-empty string.")
    if not isinstance(data.get("seed"), int):
        raise ScenarioError("seed must be an integer.")

    for section_name in ("floor", "lighting", "camera", "target"):
        if not isinstance(data.get(section_name), dict):
            raise ScenarioError(f"{section_name} must be a mapping.")

    floor = data["floor"]
    floor["size"] = _numeric_vector(floor.get("size"), 3, "floor.size")
    floor["color"] = _numeric_vector(floor.get("color"), 4, "floor.color")
    if any(value <= 0 for value in floor["size"]):
        raise ScenarioError("floor.size values must be positive.")

    lighting = data["lighting"]
    for field, length in (("ambient", 4), ("background", 4), ("diffuse", 4), ("direction", 3)):
        lighting[field] = _numeric_vector(lighting.get(field), length, f"lighting.{field}")
    if not isinstance(lighting.get("shadows"), bool):
        raise ScenarioError("lighting.shadows must be true or false.")

    camera = data["camera"]
    camera["pose"] = _numeric_vector(camera.get("pose"), 6, "camera.pose")
    if not isinstance(camera.get("topic"), str) or not camera["topic"].startswith("/"):
        raise ScenarioError("camera.topic must be an absolute topic name.")
    for field in ("update_rate_hz", "horizontal_fov_rad", "near_clip_m", "far_clip_m"):
        value = camera.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            raise ScenarioError(f"camera.{field} must be a positive number.")
    for field in ("width", "height"):
        if not isinstance(camera.get(field), int) or camera[field] <= 0:
            raise ScenarioError(f"camera.{field} must be a positive integer.")
    if camera["near_clip_m"] >= camera["far_clip_m"]:
        raise ScenarioError("camera.near_clip_m must be less than far_clip_m.")

    target = data["target"]
    target["pose"] = _numeric_vector(target.get("pose"), 6, "target.pose")
    target["size"] = _numeric_vector(target.get("size"), 3, "target.size")
    target["color"] = _numeric_vector(target.get("color"), 4, "target.color")
    if any(value <= 0 for value in target["size"]):
        raise ScenarioError("target.size values must be positive.")

    obstacles = data.get("obstacles")
    if not isinstance(obstacles, list):
        raise ScenarioError("obstacles must be a list.")
    names: set[str] = set()
    for index, obstacle in enumerate(obstacles):
        if not isinstance(obstacle, dict):
            raise ScenarioError(f"obstacles[{index}] must be a mapping.")
        obstacle_name = obstacle.get("name")
        if not isinstance(obstacle_name, str) or not SCENARIO_NAME.fullmatch(obstacle_name):
            raise ScenarioError(f"obstacles[{index}].name is invalid.")
        if obstacle_name in names:
            raise ScenarioError(f"Duplicate obstacle name: {obstacle_name}.")
        names.add(obstacle_name)
        for field, length in VECTOR_LENGTHS.items():
            obstacle[field] = _numeric_vector(
                obstacle.get(field), length, f"obstacles[{index}].{field}"
            )
        if any(value <= 0 for value in obstacle["size"]):
            raise ScenarioError(f"obstacles[{index}].size values must be positive.")


def _numbers(values: list[float]) -> str:
    return " ".join(f"{value:.10g}" for value in values)


def _add_box_model(
    world: ET.Element,
    *,
    name: str,
    pose: list[float],
    size: list[float],
    color: list[float],
) -> None:
    model = ET.SubElement(world, "model", {"name": name})
    ET.SubElement(model, "static").text = "true"
    ET.SubElement(model, "pose").text = _numbers(pose)
    link = ET.SubElement(model, "link", {"name": "link"})
    collision = ET.SubElement(link, "collision", {"name": "collision"})
    collision_box = ET.SubElement(ET.SubElement(collision, "geometry"), "box")
    ET.SubElement(collision_box, "size").text = _numbers(size)
    visual = ET.SubElement(link, "visual", {"name": "visual"})
    visual_box = ET.SubElement(ET.SubElement(visual, "geometry"), "box")
    ET.SubElement(visual_box, "size").text = _numbers(size)
    material = ET.SubElement(visual, "material")
    ET.SubElement(material, "ambient").text = _numbers(color)
    ET.SubElement(material, "diffuse").text = _numbers(color)


def build_sdf(data: dict[str, Any]) -> str:
    """Return a complete deterministic SDF world for a validated scenario."""
    validate_scenario(data)
    root = ET.Element("sdf", {"version": "1.9"})
    world = ET.SubElement(root, "world", {"name": data["name"]})
    world.append(ET.Comment(f"seed={data['seed']} scope={data['evidence_scope']}"))

    physics = ET.SubElement(world, "physics", {"name": "scenario_physics", "type": "ignored"})
    ET.SubElement(physics, "max_step_size").text = "0.005"
    ET.SubElement(physics, "real_time_factor").text = "1.0"
    for filename, name in (
        ("gz-sim-physics-system", "gz::sim::systems::Physics"),
        ("gz-sim-user-commands-system", "gz::sim::systems::UserCommands"),
        ("gz-sim-scene-broadcaster-system", "gz::sim::systems::SceneBroadcaster"),
    ):
        ET.SubElement(world, "plugin", {"filename": filename, "name": name})
    sensors = ET.SubElement(
        world,
        "plugin",
        {"filename": "gz-sim-sensors-system", "name": "gz::sim::systems::Sensors"},
    )
    ET.SubElement(sensors, "render_engine").text = "ogre2"
    ET.SubElement(world, "gravity").text = "0 0 -9.81"

    lighting = data["lighting"]
    scene = ET.SubElement(world, "scene")
    ET.SubElement(scene, "ambient").text = _numbers(lighting["ambient"])
    ET.SubElement(scene, "background").text = _numbers(lighting["background"])
    ET.SubElement(scene, "shadows").text = str(lighting["shadows"]).lower()
    light = ET.SubElement(world, "light", {"name": "warehouse_light", "type": "directional"})
    ET.SubElement(light, "cast_shadows").text = str(lighting["shadows"]).lower()
    ET.SubElement(light, "pose").text = "0 0 12 0 0 0"
    ET.SubElement(light, "diffuse").text = _numbers(lighting["diffuse"])
    ET.SubElement(light, "specular").text = "0.1 0.1 0.1 1"
    ET.SubElement(light, "direction").text = _numbers(lighting["direction"])

    floor = data["floor"]
    floor_pose = [0.0, 0.0, -floor["size"][2] / 2.0, 0.0, 0.0, 0.0]
    _add_box_model(
        world,
        name="warehouse_floor",
        pose=floor_pose,
        size=floor["size"],
        color=floor["color"],
    )
    for obstacle in data["obstacles"]:
        _add_box_model(world, **obstacle)

    camera_data = data["camera"]
    camera_model = ET.SubElement(world, "model", {"name": "camera_rig"})
    ET.SubElement(camera_model, "static").text = "true"
    ET.SubElement(camera_model, "pose").text = _numbers(camera_data["pose"])
    camera_link = ET.SubElement(camera_model, "link", {"name": "camera_link"})
    sensor = ET.SubElement(camera_link, "sensor", {"name": "front_camera", "type": "camera"})
    ET.SubElement(sensor, "topic").text = camera_data["topic"]
    ET.SubElement(sensor, "update_rate").text = str(camera_data["update_rate_hz"])
    ET.SubElement(sensor, "always_on").text = "true"
    ET.SubElement(sensor, "visualize").text = "true"
    camera = ET.SubElement(sensor, "camera")
    ET.SubElement(camera, "horizontal_fov").text = str(camera_data["horizontal_fov_rad"])
    image = ET.SubElement(camera, "image")
    ET.SubElement(image, "width").text = str(camera_data["width"])
    ET.SubElement(image, "height").text = str(camera_data["height"])
    ET.SubElement(image, "format").text = "R8G8B8"
    clip = ET.SubElement(camera, "clip")
    ET.SubElement(clip, "near").text = str(camera_data["near_clip_m"])
    ET.SubElement(clip, "far").text = str(camera_data["far_clip_m"])

    target = data["target"]
    _add_box_model(
        world,
        name="visual_target",
        pose=target["pose"],
        size=target["size"],
        color=target["color"],
    )
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def render_scenario(source: Path, output_dir: Path) -> dict[str, Any]:
    """Render an SDF and manifest, returning their paths and identifiers."""
    data, sources = load_scenario(source)
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    config_hash = hashlib.sha256(canonical).hexdigest()
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{data['name']}-{config_hash[:12]}"
    world_path = output_dir / f"{stem}.sdf"
    manifest_path = output_dir / f"{stem}.json"
    world_path.write_text(build_sdf(data), encoding="utf-8")
    manifest = {
        "scenario": data["name"],
        "schema_version": data["schema_version"],
        "seed": data["seed"],
        "config_sha256": config_hash,
        "source_files": [str(path) for path in sources],
        "world_path": str(world_path),
        "evidence_scope": data["evidence_scope"],
        "variable_under_test": data["variable_under_test"],
        "expected_visibility": data["expected_visibility"],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(render_scenario(args.scenario, args.output_dir), indent=2))


if __name__ == "__main__":
    main()
