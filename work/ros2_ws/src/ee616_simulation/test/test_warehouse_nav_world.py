from pathlib import Path

import pytest

from ee616_simulation.warehouse_nav_world import (
    MAP_HEIGHT,
    MAP_WIDTH,
    NAV_CAMERA_HORIZONTAL_FOV_RAD,
    WAREHOUSE_LAYOUTS,
    build_warehouse_nav_world,
    render_warehouse_nav_map,
    warehouse_layout,
    warehouse_world_name,
)


@pytest.mark.parametrize("follower_count", [1, 2, 3])
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
    assert world.count(
        f"<horizontal_fov>{NAV_CAMERA_HORIZONTAL_FOV_RAD}</horizontal_fov>"
    ) == follower_count
    assert world.count("wraparound_predecessor_target_") == 3 * (follower_count + 1)


def test_world_rejects_unapproved_chain_size():
    with pytest.raises(ValueError):
        build_warehouse_nav_world(4)


def test_two_real_layouts_change_shelves_and_world_identity():
    standard = build_warehouse_nav_world(1, "standard")
    sparse = build_warehouse_nav_world(1, "sparse")
    assert set(WAREHOUSE_LAYOUTS) == {"standard", "sparse"}
    assert standard.count("shelf_row_") == 9
    assert sparse.count("shelf_row_") == 6
    assert warehouse_world_name(1, "standard") in standard
    assert warehouse_world_name(1, "sparse") in sparse
    with pytest.raises(ValueError):
        warehouse_layout("../../outside")


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


def test_layout_maps_have_distinct_content(tmp_path: Path):
    standard = render_warehouse_nav_map(tmp_path, "standard")
    sparse = render_warehouse_nav_map(tmp_path, "sparse")
    assert standard != sparse
    standard_image = Path(standard.read_text().splitlines()[0].split(":", 1)[1].strip())
    sparse_image = Path(sparse.read_text().splitlines()[0].split(":", 1)[1].strip())
    assert standard_image.read_bytes() != sparse_image.read_bytes()
