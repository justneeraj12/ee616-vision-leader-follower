"""Generate the mapped multi-aisle warehouse used by the Nav2 mission."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ee616_simulation.warehouse_mission_world import (
    _cargo_robot,
    _shelf,
    _station_model,
)


WORLD_NAME_PREFIX = "warehouse_nav_mission"
LOADING_STATION = (-10.0, -6.0)
DROPOFF_STATION = (-10.0, -1.0)
SHELF_X = (-3.0, 0.0, 3.0)
SHELF_Y = (-3.5, 2.0, 7.5)
MAP_ORIGIN = (-19.0, -12.0)
MAP_RESOLUTION = 0.10
MAP_WIDTH = 380
MAP_HEIGHT = 240
LIDAR_HEIGHT_M = 0.90


def _nav_leader(x: float, y: float) -> str:
    """Return the route-owning leader with a low-cost planar lidar."""
    robot = _cargo_robot("leader", x, y=y, camera=False)
    lidar = f"""
        <sensor name="navigation_lidar" type="gpu_lidar">
          <!-- The scan plane stays above the presentation cargo box so the
               leader does not mistake its own load for an obstacle. -->
          <pose>0 0 {LIDAR_HEIGHT_M} 0 0 0</pose>
          <topic>/leader/scan</topic>
          <update_rate>10</update_rate><always_on>true</always_on>
          <lidar>
            <scan><horizontal>
              <samples>360</samples><resolution>1</resolution>
              <min_angle>-3.1415926536</min_angle>
              <max_angle>3.1415926536</max_angle>
            </horizontal></scan>
            <range><min>0.10</min><max>18.0</max><resolution>0.02</resolution></range>
          </lidar>
        </sensor>
"""
    needle = "      </link>\n      <link name=\"left_wheel\">"
    return robot.replace(needle, f"{lidar}      </link>\n      <link name=\"left_wheel\">", 1)


def _aisle_stripe(name: str, x: float, y: float, sx: float, sy: float) -> str:
    return f"""
    <model name="{name}"><static>true</static><pose>{x} {y} 0.006 0 0 0</pose>
      <link name="link"><visual name="visual">
        <geometry><box><size>{sx} {sy} 0.01</size></box></geometry>
        <material><ambient>0.78 0.69 0.16 1</ambient><diffuse>0.88 0.78 0.18 1</diffuse></material>
      </visual></link>
    </model>"""


def _warehouse_wall(
    name: str,
    x: float,
    y: float,
    size_x: float,
    size_y: float,
) -> str:
    return f"""
    <model name="{name}"><static>true</static><pose>{x} {y} 1.25 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>{size_x} {size_y} 2.5</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>{size_x} {size_y} 2.5</size></box></geometry>
          <material>
            <ambient>0.20 0.24 0.29 1</ambient>
            <diffuse>0.26 0.31 0.37 1</diffuse>
          </material>
        </visual>
      </link>
    </model>"""


def build_warehouse_nav_world(follower_count: int) -> str:
    """Return a logical receiving-to-dispatch warehouse with three shelf rows."""
    if follower_count not in {1, 3}:
        raise ValueError("follower_count must be 1 or 3")
    robots = [_nav_leader(-10.0, -6.0)]
    robots.extend(
        _cargo_robot(
            f"follower_{index}",
            -10.0 - 2.0 * index,
            y=-6.0,
            camera=True,
        )
        for index in range(1, follower_count + 1)
    )
    shelves = "".join(
        _shelf(
            f"shelf_row_{row}_bay_{column}",
            x,
            y,
        )
        for row, y in enumerate(SHELF_Y, start=1)
        for column, x in enumerate(SHELF_X, start=1)
    )
    stripes = "".join(
        _aisle_stripe(f"aisle_{index}", 0.0, y, 15.0, 0.06)
        for index, y in enumerate((-6.0, -1.0, 4.75, 10.0), start=1)
    )
    loading_station = _station_model(
        "receiving_loading_dock",
        *LOADING_STATION,
        color="0.04 0.46 0.82 1",
        label_color="0.05 0.63 0.96 1",
    )
    dropoff_station = _station_model(
        "dispatch_dropoff_dock",
        *DROPOFF_STATION,
        color="0.08 0.64 0.28 1",
        label_color="0.12 0.80 0.38 1",
    )
    perimeter = "".join([
        _warehouse_wall("west_wall", -18.85, 0.0, 0.30, 24.0),
        _warehouse_wall("east_wall", 18.85, 0.0, 0.30, 24.0),
        _warehouse_wall("south_wall", 0.0, -11.85, 38.0, 0.30),
        _warehouse_wall("north_wall", 0.0, 11.85, 38.0, 0.30),
    ])
    return f"""<?xml version="1.0"?>
<sdf version="1.9">
  <world name="{WORLD_NAME_PREFIX}_{follower_count}">
    <physics name="navigation_physics" type="ignored">
      <max_step_size>0.005</max_step_size><real_time_factor>1.0</real_time_factor>
    </physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <gravity>0 0 -9.81</gravity>
    <scene>
      <ambient>0.58 0.58 0.58 1</ambient><background>0.09 0.12 0.16 1</background>
      <shadows>false</shadows><grid>false</grid>
    </scene>
    <light name="warehouse_light" type="directional">
      <pose>0 0 14 0 0 0</pose><cast_shadows>false</cast_shadows>
      <diffuse>0.92 0.92 0.92 1</diffuse><specular>0.08 0.08 0.08 1</specular>
      <direction>-0.25 0.15 -0.95</direction>
    </light>
    <model name="warehouse_floor"><static>true</static><pose>0 0 -0.05 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>38 24 0.1</size></box></geometry>
        </collision>
        <visual name="visual"><geometry><box><size>38 24 0.1</size></box></geometry>
          <material>
            <ambient>0.34 0.37 0.40 1</ambient>
            <diffuse>0.40 0.43 0.46 1</diffuse>
          </material>
        </visual>
      </link>
    </model>
    {perimeter}
    {loading_station}
    {dropoff_station}
    {stripes}
    {shelves}
    {''.join(robots)}
    <gui fullscreen="false">
      <camera name="warehouse_three_quarter">
        <pose>-3.0 -17.5 12.0 0 0.53 1.36</pose>
      </camera>
    </gui>
  </world>
</sdf>
"""


def render_warehouse_nav_world(follower_count: int, output_dir: Path) -> Path:
    """Write a content-addressed navigation world and return its path."""
    text = build_warehouse_nav_world(follower_count)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{WORLD_NAME_PREFIX}_{follower_count}-{digest}.sdf"
    path.write_text(text, encoding="utf-8")
    return path


def _occupied(x: float, y: float) -> bool:
    """Return whether one map cell belongs to a wall or shelf footprint."""
    if abs(x) >= 18.7 or abs(y) >= 11.7:
        return True
    return any(
        # Measured from the vendored AWS ShelfE collision mesh after its
        # COLLADA transform: approximately 3.92 m long by 0.88 m deep.
        abs(x - shelf_x) <= 1.98 and abs(y - shelf_y) <= 0.48
        for shelf_x in SHELF_X
        for shelf_y in SHELF_Y
    )


def render_warehouse_nav_map(output_dir: Path) -> Path:
    """Write the deterministic static occupancy map and return its YAML path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[str] = []
    origin_x, origin_y = MAP_ORIGIN
    for row in range(MAP_HEIGHT):
        y = origin_y + (MAP_HEIGHT - row - 0.5) * MAP_RESOLUTION
        values = []
        for column in range(MAP_WIDTH):
            x = origin_x + (column + 0.5) * MAP_RESOLUTION
            values.append("0" if _occupied(x, y) else "254")
        rows.append(" ".join(values))
    image_text = f"P2\n{MAP_WIDTH} {MAP_HEIGHT}\n255\n" + "\n".join(rows) + "\n"
    digest = hashlib.sha256(image_text.encode("ascii")).hexdigest()[:12]
    image_path = output_dir / f"warehouse_nav-{digest}.pgm"
    yaml_path = output_dir / f"warehouse_nav-{digest}.yaml"
    image_path.write_text(image_text, encoding="ascii")
    yaml_path.write_text(
        "\n".join([
            f"image: {image_path}",
            f"resolution: {MAP_RESOLUTION}",
            f"origin: [{origin_x}, {origin_y}, 0.0]",
            "negate: 0",
            "occupied_thresh: 0.65",
            "free_thresh: 0.25",
            "mode: trinary",
            "",
        ]),
        encoding="utf-8",
    )
    return yaml_path
