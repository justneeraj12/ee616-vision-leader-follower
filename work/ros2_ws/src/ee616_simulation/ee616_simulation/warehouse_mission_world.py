"""Generate the optimized visual warehouse used by the cargo mission."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ee616_simulation.pair_world import _robot


LOADING_STATION = (-5.0, 0.0)
DROPOFF_STATION = (12.3, 3.9)


def _cargo_robot(
    name: str,
    x: float,
    *,
    camera: bool,
    y: float = 0.0,
) -> str:
    """Return a differential-drive robot with a presentation-only cargo lift."""
    robot = _robot(name, x, camera=camera, target=True)
    robot = robot.replace(
        f"<pose>{x} 0 0 0 0 0</pose>",
        f"<pose>{x} {y} 0 0 0 0</pose>",
        1,
    )
    cargo_xml = f"""
      <link name="cargo_link">
        <pose>0 0 -1.0 0 0 0</pose>
        <inertial>
          <mass>0.05</mass>
          <inertia><ixx>0.0001</ixx><iyy>0.0001</iyy><izz>0.0001</izz></inertia>
        </inertial>
        <visual name="cargo_visual">
          <geometry><box><size>0.42 0.32 0.25</size></box></geometry>
          <material>
            <!-- Blue cargo is deliberately distinct from the red-orange
                 predecessor marker used by the learned detector. -->
            <ambient>0.03 0.48 0.88 1</ambient>
            <diffuse>0.05 0.60 1.0 1</diffuse>
          </material>
        </visual>
      </link>
      <joint name="cargo_lift_joint" type="prismatic">
        <parent>base_link</parent><child>cargo_link</child>
        <axis><xyz>0 0 1</xyz><limit><lower>0</lower><upper>1.52</upper></limit></axis>
      </joint>
      <plugin filename="gz-sim-joint-position-controller-system"
              name="gz::sim::systems::JointPositionController">
        <joint_name>cargo_lift_joint</joint_name>
        <topic>/warehouse_mission/{name}/cargo_position</topic>
        <p_gain>12.0</p_gain><i_gain>0.0</i_gain><d_gain>2.0</d_gain>
        <cmd_max>5.0</cmd_max><cmd_min>-5.0</cmd_min>
      </plugin>
"""
    return robot.replace("    </model>", f"{cargo_xml}    </model>", 1)


def _station_model(
    name: str,
    x: float,
    y: float,
    *,
    color: str,
    label_color: str,
) -> str:
    """Return a low-cost floor pad and raised sign for visual orientation."""
    return f"""
    <model name="{name}"><static>true</static><pose>{x} {y} 0 0 0 0</pose>
      <link name="pad">
        <visual name="pad_visual"><pose>0 0 0.011 0 0 0</pose>
          <geometry><box><size>1.4 1.4 0.02</size></box></geometry>
          <material><ambient>{color}</ambient><diffuse>{color}</diffuse></material>
        </visual>
      </link>
      <link name="sign"><pose>0 1.15 1.0 0 0 0</pose>
        <visual name="post"><pose>0 0 -0.45 0 0 0</pose>
          <geometry><box><size>0.08 0.08 1.0</size></box></geometry>
          <material><ambient>0.16 0.18 0.20 1</ambient><diffuse>0.20 0.22 0.24 1</diffuse></material>
        </visual>
        <visual name="board">
          <geometry><box><size>0.10 1.2 0.55</size></box></geometry>
          <material><ambient>{label_color}</ambient><diffuse>{label_color}</diffuse></material>
        </visual>
      </link>
    </model>"""


def _shelf(name: str, x: float, y: float, *, yaw: float = 0.0) -> str:
    return f"""
    <include>
      <uri>model://aws_robomaker_warehouse_ShelfE_01</uri>
      <name>{name}</name><pose>{x} {y} 0 0 0 {yaw}</pose>
    </include>"""


def build_warehouse_mission_world(follower_count: int) -> str:
    """Return the one-pair or three-follower mid-size warehouse world."""
    if follower_count not in {1, 3}:
        raise ValueError("follower_count must be 1 or 3")
    robots = [_cargo_robot("leader", -5.0, camera=False)]
    robots.extend(
        _cargo_robot(f"follower_{index}", -5.0 - 2.0 * index, camera=True)
        for index in range(1, follower_count + 1)
    )
    shelves = "".join(
        _shelf(f"shelf_{row}_{column}", x, y)
        for row, y in (("south", -4.5), ("north", 4.5))
        for column, x in enumerate((-1.5, 2.5, 6.5), start=1)
    )
    return f"""<?xml version="1.0"?>
<sdf version="1.9">
  <world name="warehouse_mission_{follower_count}">
    <physics name="mission_physics" type="ignored">
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
      <ambient>0.55 0.55 0.55 1</ambient><background>0.10 0.13 0.17 1</background>
      <shadows>false</shadows><grid>false</grid>
    </scene>
    <light name="warehouse_light" type="directional">
      <pose>0 0 12 0 0 0</pose><cast_shadows>false</cast_shadows>
      <diffuse>0.9 0.9 0.9 1</diffuse><specular>0.1 0.1 0.1 1</specular>
      <direction>-0.3 0.2 -0.9</direction>
    </light>
    <model name="warehouse_floor"><static>true</static><pose>0 0 -0.05 0 0 0</pose>
      <link name="link">
        <collision name="collision"><geometry><box><size>30 22 0.1</size></box></geometry></collision>
        <visual name="visual"><geometry><box><size>30 22 0.1</size></box></geometry>
          <material><ambient>0.38 0.40 0.42 1</ambient><diffuse>0.44 0.46 0.48 1</diffuse></material>
        </visual>
      </link>
    </model>
    <model name="center_aisle"><static>true</static><pose>3.0 0 0.006 0 0 0</pose>
      <link name="link"><visual name="visual">
        <geometry><box><size>22 2.8 0.01</size></box></geometry>
        <material><ambient>0.18 0.24 0.29 1</ambient><diffuse>0.20 0.27 0.32 1</diffuse></material>
      </visual></link>
    </model>
    {_station_model("loading_station", *LOADING_STATION, color="0.04 0.50 0.82 1", label_color="0.05 0.64 0.95 1")}
    {_station_model("dropoff_station", *DROPOFF_STATION, color="0.10 0.67 0.31 1", label_color="0.12 0.78 0.38 1")}
    {shelves}
    {''.join(robots)}
    <gui fullscreen="false">
      <camera name="overview"><pose>2.0 -18.0 17.0 0 0.65 1.57</pose></camera>
    </gui>
  </world>
</sdf>
"""


def render_warehouse_mission_world(follower_count: int, output_dir: Path) -> Path:
    """Write a content-addressed mission world and return its path."""
    text = build_warehouse_mission_world(follower_count)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"warehouse_mission_{follower_count}-{digest}.sdf"
    path.write_text(text, encoding="utf-8")
    return path
