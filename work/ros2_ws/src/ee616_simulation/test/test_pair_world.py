import xml.etree.ElementTree as ET

import pytest

from ee616_simulation.pair_world import (
    build_chain_world,
    build_disturbance_world,
    build_pair_world,
)


@pytest.mark.parametrize("profile", ["straight", "turn"])
def test_pair_world_has_two_namespaced_robots(profile):
    root = ET.fromstring(build_pair_world(profile))
    world = root.find("world")
    assert world is not None
    assert world.attrib["name"] == f"pair_{profile}"
    models = {model.attrib["name"]: model for model in world.findall("model")}
    assert {"leader", "follower_1"}.issubset(models)
    text = build_pair_world(profile)
    assert "/leader/cmd_vel" in text
    assert "/leader/odom" in text
    assert "/follower_1/cmd_vel" in text
    assert "/follower_1/odom" in text
    assert "/follower_1/camera/image" in text


def test_pair_world_rejects_unapproved_profile():
    with pytest.raises(ValueError):
        build_pair_world("occlusion")


@pytest.mark.parametrize("follower_count", [2, 3])
def test_chain_world_adds_followers_incrementally(follower_count):
    text = build_chain_world("turn", follower_count)
    root = ET.fromstring(text)
    world = root.find("world")
    assert world is not None
    assert world.attrib["name"] == f"chain_{follower_count}_turn"
    names = {model.attrib["name"] for model in world.findall("model")}
    for index in range(1, follower_count + 1):
        assert f"follower_{index}" in names
        assert f"/follower_{index}/camera/image" in text
    assert f"follower_{follower_count + 1}" not in names


def test_chain_world_rejects_nonincremental_size():
    with pytest.raises(ValueError):
        build_chain_world("straight", 4)


@pytest.mark.parametrize("follower_count", [1, 3])
def test_disturbance_world_has_traceable_name(follower_count):
    text = build_disturbance_world("long_occlusion", follower_count)
    root = ET.fromstring(text)
    assert root.find("world").attrib["name"] == f"disturbance_{follower_count}_long_occlusion"


def test_disturbance_world_rejects_unapproved_scenario():
    with pytest.raises(ValueError):
        build_disturbance_world("random_fault", 1)
