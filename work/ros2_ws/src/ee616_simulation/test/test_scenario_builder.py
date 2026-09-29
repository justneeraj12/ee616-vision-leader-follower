import json
import xml.etree.ElementTree as ET
from pathlib import Path

from ee616_simulation.aws_world import prepare_aws_world
from ee616_simulation.scenario_builder import ScenarioError, load_scenario, render_scenario
import pytest


PACKAGE_ROOT = Path(__file__).parents[1]
SCENARIO_ROOT = PACKAGE_ROOT / "scenarios"
VENDOR_ROOT = PACKAGE_ROOT / "vendor" / "aws_small_warehouse"


def test_every_scenario_renders_valid_deterministic_sdf(tmp_path):
    scenarios = sorted(path for path in SCENARIO_ROOT.glob("*.yaml") if path.stem != "base")
    assert [path.stem for path in scenarios] == [
        "camera_calibration",
        "narrow_aisle",
        "partial_occlusion",
        "right_angle_turn",
        "straight_aisle",
    ]
    for source in scenarios:
        first = render_scenario(source, tmp_path)
        second = render_scenario(source, tmp_path)
        assert first["config_sha256"] == second["config_sha256"]
        assert first["world_path"] == second["world_path"]
        root = ET.parse(first["world_path"]).getroot()
        assert root.find("world/model[@name='camera_rig']") is not None
        assert root.find("world/model[@name='visual_target']") is not None
        manifest = json.loads(Path(first["manifest_path"]).read_text(encoding="utf-8"))
        assert manifest["scenario"] == source.stem
        assert manifest["evidence_scope"].endswith("only.")


def test_scenario_inheritance_cannot_escape_directory(tmp_path):
    scenario = tmp_path / "unsafe.yaml"
    scenario.write_text("extends: ../base.yaml\nname: unsafe\n", encoding="utf-8")
    with pytest.raises(ScenarioError, match="scenario directory"):
        load_scenario(scenario)


def test_aws_world_is_pinned_and_augmented_without_changing_source(tmp_path):
    source = VENDOR_ROOT / "worlds" / "no_roof_small_warehouse" / "no_roof_small_warehouse.world"
    original = source.read_bytes()
    result = prepare_aws_world(source, tmp_path)
    assert source.read_bytes() == original
    assert result["source_sha256"]
    root = ET.parse(result["world_path"]).getroot()
    world = root.find("world")
    assert world is not None
    assert world.get("name") == "aws_no_roof_warehouse"
    assert world.find("model[@name='ee616_benchmark_camera']") is not None
    assert world.find("model[@name='ee616_visual_target']") is not None
    assert (VENDOR_ROOT / "LICENSE").is_file()
    assert (VENDOR_ROOT / "SOURCE.md").is_file()
