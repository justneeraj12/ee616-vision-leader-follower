from pathlib import Path

import pytest

from ee616_simulation.warehouse_nav_world import (
    MAP_HEIGHT,
    MAP_WIDTH,
    build_warehouse_nav_world,
    render_warehouse_nav_map,
)


@pytest.mark.parametrize("follower_count", [1, 3])
def test_world_has_logical_stations_rows_and_lidar(follower_count):
    world = build_warehouse_nav_world(follower_count)
    assert "receiving_loading_dock" in world
    assert "dispatch_dropoff_dock" in world
    assert "navigation_lidar" in world
    assert "/leader/scan" in world
    assert "{LIDAR_HEIGHT_M}" not in world
    assert world.count("shelf_row_") == 9
    assert world.count('_wall"') == 4
    assert world.count("front_camera") == follower_count


def test_world_rejects_unapproved_chain_size():
    with pytest.raises(ValueError):
        build_warehouse_nav_world(2)


def test_map_is_deterministic_and_contains_obstacles(tmp_path: Path):
    first = render_warehouse_nav_map(tmp_path)
    second = render_warehouse_nav_map(tmp_path)
    assert first == second
    image_path = Path(
        next(line for line in first.read_text().splitlines() if line.startswith("image:"))
        .split(":", 1)[1]
        .strip()
    )
    lines = image_path.read_text(encoding="ascii").splitlines()
    assert lines[0] == "P2"
    assert lines[1] == f"{MAP_WIDTH} {MAP_HEIGHT}"
    pixels = " ".join(lines[3:]).split()
    assert len(pixels) == MAP_WIDTH * MAP_HEIGHT
    assert "0" in pixels
    assert "254" in pixels
