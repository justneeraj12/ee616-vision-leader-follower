"""Generate the mapped multi-aisle warehouse used by the Nav2 mission."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
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
NAV_CAMERA_HORIZONTAL_FOV_RAD = 2.0943951024


@dataclass(frozen=True)
class WarehouseLayout:
    """Deterministic shelf arrangement sharing the verified map boundary."""

    label: str
    shelf_x: tuple[float, ...]
    shelf_y: tuple[float, ...]
    description: str


WAREHOUSE_LAYOUTS = {
    "standard": WarehouseLayout(
        "Nine-shelf warehouse",
        SHELF_X,
        SHELF_Y,
        "Three rows with three shelf blocks per row.",
    ),
    "sparse": WarehouseLayout(
        "Six-shelf flexible warehouse",
        (-4.5, 4.5),
        SHELF_Y,
        "Three rows with a removable center bay and wider internal openings.",
    ),
}


def warehouse_layout(profile: str) -> WarehouseLayout:
    """Return one bounded warehouse layout profile."""
    try:
        return WAREHOUSE_LAYOUTS[profile]
    except KeyError as error:
        choices = ", ".join(sorted(WAREHOUSE_LAYOUTS))
        raise ValueError(f"map_profile must be one of: {choices}") from error


def warehouse_world_name(follower_count: int, map_profile: str) -> str:
    """Return a stable Gazebo world name for an evaluated profile."""
    suffix = "" if map_profile == "standard" else f"_{map_profile}"
    return f"{WORLD_NAME_PREFIX}{suffix}_{follower_count}"


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
    robot = robot.replace(
        needle,
        f"{lidar}      </link>\n      <link name=\"left_wheel\">",
        1,
    )
    return _with_wraparound_target(robot)


def _with_wraparound_target(robot: str) -> str:
    """Add a known-height visual beacon that remains visible through turns."""
    beacon = """
        <!-- The original rear panel remains unchanged. These three flat,
             known-height faces preserve the trained target appearance when
             the predecessor rotates through a warehouse corner. -->
        <visual name="wraparound_predecessor_target_left">
          <pose>-0.02 0.25 0.38 0 0 0</pose>
          <geometry><box><size>0.70 0.04 0.90</size></box></geometry>
          <material><ambient>0.9 0.15 0.05 1</ambient><diffuse>0.9 0.15 0.05 1</diffuse></material>
        </visual>
        <visual name="wraparound_predecessor_target_right">
          <pose>-0.02 -0.25 0.38 0 0 0</pose>
          <geometry><box><size>0.70 0.04 0.90</size></box></geometry>
          <material><ambient>0.9 0.15 0.05 1</ambient><diffuse>0.9 0.15 0.05 1</diffuse></material>
        </visual>
        <visual name="wraparound_predecessor_target_front">
          <pose>0.30 0 0.38 0 0 0</pose>
          <geometry><box><size>0.04 0.70 0.90</size></box></geometry>
          <material><ambient>0.9 0.15 0.05 1</ambient><diffuse>0.9 0.15 0.05 1</diffuse></material>
        </visual>
"""
    needle = "      </link>\n      <link name=\"left_wheel\">"
    return robot.replace(
        needle,
        f"{beacon}      </link>\n      <link name=\"left_wheel\">",
        1,
    )


def _with_nav_wide_angle_camera(robot: str) -> str:
    """Use a 120-degree forward RGB camera for mapped warehouse turns."""
    return robot.replace(
        "<horizontal_fov>1.2217304764</horizontal_fov>",
        f"<horizontal_fov>{NAV_CAMERA_HORIZONTAL_FOV_RAD}</horizontal_fov>",
        1,
    )


def _with_industrial_visuals(robot: str, name: str) -> str:
    """Add a presentation shell without changing dynamics or sensor geometry."""
    if name == "leader":
        primary = "0.20 0.36 0.30 1"
        accent = "0.45 0.66 0.52 1"
    else:
        palette = {
            "follower_1": ("0.20 0.27 0.31 1", "0.22 0.52 0.67 1"),
            "follower_2": ("0.22 0.27 0.25 1", "0.43 0.62 0.49 1"),
            "follower_3": ("0.28 0.27 0.22 1", "0.68 0.55 0.28 1"),
        }
        primary, accent = palette.get(
            name, ("0.22 0.27 0.25 1", "0.43 0.62 0.49 1")
        )
    shell = f"""
        <!-- Visual-only industrial cart shell. Collision, inertia, wheels,
             cameras, LiDAR, and learned-target geometry remain unchanged. -->
        <visual name="industrial_lower_skirt">
          <pose>0 0 -0.035 0 0 0</pose>
          <geometry><box><size>0.58 0.46 0.14</size></box></geometry>
          <material><ambient>{primary}</ambient><diffuse>{primary}</diffuse></material>
        </visual>
        <visual name="industrial_upper_deck">
          <pose>-0.01 0 0.15 0 0 0</pose>
          <geometry><box><size>0.52 0.38 0.08</size></box></geometry>
          <material><ambient>0.08 0.10 0.11 1</ambient><diffuse>0.12 0.14 0.15 1</diffuse></material>
        </visual>
        <visual name="industrial_front_bumper">
          <pose>0.285 0 -0.04 0 0 0</pose>
          <geometry><box><size>0.03 0.48 0.13</size></box></geometry>
          <material><ambient>{accent}</ambient><diffuse>{accent}</diffuse><emissive>0.04 0.08 0.06 1</emissive></material>
        </visual>
        <visual name="industrial_sensor_hood">
          <pose>0.20 0 0.25 0 0 0</pose>
          <geometry><box><size>0.13 0.28 0.13</size></box></geometry>
          <material><ambient>{primary}</ambient><diffuse>{primary}</diffuse></material>
        </visual>
        <visual name="industrial_status_left">
          <pose>0.08 0.211 0.09 0 0 0</pose>
          <geometry><box><size>0.22 0.012 0.035</size></box></geometry>
          <material><ambient>{accent}</ambient><diffuse>{accent}</diffuse><emissive>{accent}</emissive></material>
        </visual>
        <visual name="industrial_status_right">
          <pose>0.08 -0.211 0.09 0 0 0</pose>
          <geometry><box><size>0.22 0.012 0.035</size></box></geometry>
          <material><ambient>{accent}</ambient><diffuse>{accent}</diffuse><emissive>{accent}</emissive></material>
        </visual>
        <visual name="industrial_status_mast">
          <pose>0 0 0.48 0 0 0</pose>
          <geometry><cylinder><radius>0.07</radius><length>0.52</length></cylinder></geometry>
          <material><ambient>0.10 0.12 0.13 1</ambient><diffuse>0.14 0.16 0.17 1</diffuse></material>
        </visual>
        <visual name="industrial_status_beacon">
          <pose>0 0 0.76 0 0 0</pose>
          <geometry><cylinder><radius>0.105</radius><length>0.08</length></cylinder></geometry>
          <material><ambient>{accent}</ambient><diffuse>{accent}</diffuse></material>
        </visual>
"""
    needle = "      </link>\n      <link name=\"left_wheel\">"
    return robot.replace(
        needle,
        f"{shell}      </link>\n      <link name=\"left_wheel\">",
        1,
    )


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


def build_warehouse_nav_world(
    follower_count: int,
    map_profile: str = "standard",
) -> str:
    """Return a logical receiving-to-dispatch warehouse with three shelf rows."""
    if follower_count not in {1, 2, 3}:
        raise ValueError("follower_count must be 1, 2, or 3")
    layout = warehouse_layout(map_profile)
    robots = [_with_industrial_visuals(
        _nav_leader(-10.0, -6.0), "leader"
    )]
    robots.extend(
        _with_industrial_visuals(
            _with_nav_wide_angle_camera(
                _with_wraparound_target(_cargo_robot(
                    f"follower_{index}",
                    -10.0 - 2.0 * index,
                    y=-6.0,
                    camera=True,
                ))
            ),
            f"follower_{index}",
        )
        for index in range(1, follower_count + 1)
    )
    shelves = "".join(
        _shelf(
            f"shelf_row_{row}_bay_{column}",
            x,
            y,
        )
        for row, y in enumerate(layout.shelf_y, start=1)
        for column, x in enumerate(layout.shelf_x, start=1)
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
  <world name="{warehouse_world_name(follower_count, map_profile)}">
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


def render_warehouse_nav_world(
    follower_count: int,
    output_dir: Path,
    map_profile: str = "standard",
) -> Path:
    """Write a content-addressed navigation world and return its path."""
    text = build_warehouse_nav_world(follower_count, map_profile)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / (
        f"{WORLD_NAME_PREFIX}_{map_profile}_{follower_count}-{digest}.sdf"
    )
    path.write_text(text, encoding="utf-8")
    return path


def _occupied(x: float, y: float, layout: WarehouseLayout) -> bool:
    """Return whether one map cell belongs to a wall or shelf footprint."""
    if abs(x) >= 18.7 or abs(y) >= 11.7:
        return True
    return any(
        # Measured from the vendored AWS ShelfE collision mesh after its
        # COLLADA transform: approximately 3.92 m long by 0.88 m deep.
        abs(x - shelf_x) <= 1.98 and abs(y - shelf_y) <= 0.48
        for shelf_x in layout.shelf_x
        for shelf_y in layout.shelf_y
    )


def render_warehouse_nav_map(
    output_dir: Path,
    map_profile: str = "standard",
) -> Path:
    """Write the deterministic static occupancy map and return its YAML path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    layout = warehouse_layout(map_profile)
    rows: list[str] = []
    origin_x, origin_y = MAP_ORIGIN
    for row in range(MAP_HEIGHT):
        y = origin_y + (MAP_HEIGHT - row - 0.5) * MAP_RESOLUTION
        values = []
        for column in range(MAP_WIDTH):
            x = origin_x + (column + 0.5) * MAP_RESOLUTION
            values.append("0" if _occupied(x, y, layout) else "254")
        rows.append(" ".join(values))
    image_text = f"P2\n{MAP_WIDTH} {MAP_HEIGHT}\n255\n" + "\n".join(rows) + "\n"
    digest = hashlib.sha256(image_text.encode("ascii")).hexdigest()[:12]
    image_path = output_dir / f"warehouse_nav-{map_profile}-{digest}.pgm"
    yaml_path = output_dir / f"warehouse_nav-{map_profile}-{digest}.yaml"
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
