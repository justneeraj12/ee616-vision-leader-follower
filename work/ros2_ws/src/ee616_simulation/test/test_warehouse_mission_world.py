import xml.etree.ElementTree as ET

import pytest

from ee616_simulation.warehouse_mission_world import (
    build_warehouse_mission_world,
)


@pytest.mark.parametrize("follower_count", [1, 3])
def test_mission_world_has_namespaced_robots_and_cargo(follower_count):
    text = build_warehouse_mission_world(follower_count)
    root = ET.fromstring(text)
    world = root.find("world")
    assert world is not None
    assert world.attrib["name"] == f"warehouse_mission_{follower_count}"
    models = {model.attrib["name"]: model for model in world.findall("model")}
    assert {"loading_station", "dropoff_station", "leader"}.issubset(models)
    for index in range(1, follower_count + 1):
        name = f"follower_{index}"
        assert name in models
        assert f"/{name}/camera/image" in text
        assert f"/warehouse_mission/{name}/cargo_position" in text
    assert "/leader/camera/image" not in text
    assert "/warehouse_mission/leader/cargo_position" in text
    assert text.count("JointPositionController") == follower_count + 1
    assert text.count("aws_robomaker_warehouse_ShelfE_01") == 6


def test_mission_world_rejects_unapproved_chain_size():
    with pytest.raises(ValueError):
        build_warehouse_mission_world(2)
