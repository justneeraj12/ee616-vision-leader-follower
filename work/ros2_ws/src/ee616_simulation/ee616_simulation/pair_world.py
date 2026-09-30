"""Generate the bounded two-robot Gazebo world used by the pair gate."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re


PAIR_PROFILES = {"straight", "turn"}
DISTURBANCE_SCENARIOS = {
    "sharp_turn", "short_occlusion", "long_occlusion",
    "leader_stop", "actuator_bias", "combined",
}


def _robot(name: str, x: float, *, camera: bool, target: bool) -> str:
    camera_xml = ""
    if camera:
        camera_xml = f"""
        <sensor name="front_camera" type="camera">
          <pose>0.28 0 0.43 0 0 0</pose>
          <topic>/{name}/camera/image</topic>
          <update_rate>15</update_rate><always_on>true</always_on>
          <camera>
            <horizontal_fov>1.2217304764</horizontal_fov>
            <image><width>640</width><height>480</height><format>R8G8B8</format></image>
            <clip><near>0.1</near><far>30</far></clip>
          </camera>
        </sensor>"""
    target_xml = ""
    if target:
        target_xml = """
        <visual name="predecessor_target">
          <pose>-0.30 0 0.38 0 0 0</pose>
          <geometry><box><size>0.08 0.70 0.90</size></box></geometry>
          <material><ambient>0.9 0.15 0.05 1</ambient><diffuse>0.9 0.15 0.05 1</diffuse></material>
        </visual>"""
    return f"""
    <model name="{name}">
      <pose>{x} 0 0 0 0 0</pose>
      <link name="base_link">
        <pose>0 0 0.22 0 0 0</pose>
        <inertial><mass>8.0</mass><inertia><ixx>0.18</ixx><iyy>0.30</iyy><izz>0.38</izz></inertia></inertial>
        <collision name="body_collision"><geometry><box><size>0.55 0.42 0.22</size></box></geometry></collision>
        <visual name="body_visual">
          <geometry><box><size>0.55 0.42 0.22</size></box></geometry>
          <material><ambient>0.12 0.18 0.28 1</ambient><diffuse>0.18 0.30 0.48 1</diffuse></material>
        </visual>
        <collision name="front_caster"><pose>0.20 0 -0.17 0 0 0</pose><geometry><sphere><radius>0.05</radius></sphere></geometry><surface><friction><ode><mu>0.02</mu><mu2>0.02</mu2></ode></friction></surface></collision>
        <collision name="rear_caster"><pose>-0.20 0 -0.17 0 0 0</pose><geometry><sphere><radius>0.05</radius></sphere></geometry><surface><friction><ode><mu>0.02</mu><mu2>0.02</mu2></ode></friction></surface></collision>
        {target_xml}
        {camera_xml}
      </link>
      <link name="left_wheel">
        <pose>0 0.23 0.10 -1.5707963268 0 0</pose>
        <inertial><mass>0.5</mass><inertia><ixx>0.003</ixx><iyy>0.003</iyy><izz>0.003</izz></inertia></inertial>
        <collision name="collision"><geometry><cylinder><radius>0.10</radius><length>0.04</length></cylinder></geometry><surface><friction><ode><mu>1.2</mu><mu2>1.2</mu2></ode></friction></surface></collision>
        <visual name="visual"><geometry><cylinder><radius>0.10</radius><length>0.04</length></cylinder></geometry><material><ambient>0.04 0.04 0.04 1</ambient><diffuse>0.08 0.08 0.08 1</diffuse></material></visual>
      </link>
      <link name="right_wheel">
        <pose>0 -0.23 0.10 -1.5707963268 0 0</pose>
        <inertial><mass>0.5</mass><inertia><ixx>0.003</ixx><iyy>0.003</iyy><izz>0.003</izz></inertia></inertial>
        <collision name="collision"><geometry><cylinder><radius>0.10</radius><length>0.04</length></cylinder></geometry><surface><friction><ode><mu>1.2</mu><mu2>1.2</mu2></ode></friction></surface></collision>
        <visual name="visual"><geometry><cylinder><radius>0.10</radius><length>0.04</length></cylinder></geometry><material><ambient>0.04 0.04 0.04 1</ambient><diffuse>0.08 0.08 0.08 1</diffuse></material></visual>
      </link>
      <joint name="left_wheel_joint" type="revolute"><parent>base_link</parent><child>left_wheel</child><axis><xyz>0 0 1</xyz><limit><lower>-1.79769e+308</lower><upper>1.79769e+308</upper></limit></axis></joint>
      <joint name="right_wheel_joint" type="revolute"><parent>base_link</parent><child>right_wheel</child><axis><xyz>0 0 1</xyz><limit><lower>-1.79769e+308</lower><upper>1.79769e+308</upper></limit></axis></joint>
      <plugin filename="gz-sim-diff-drive-system" name="gz::sim::systems::DiffDrive">
        <left_joint>left_wheel_joint</left_joint><right_joint>right_wheel_joint</right_joint>
        <wheel_separation>0.46</wheel_separation><wheel_radius>0.10</wheel_radius>
        <topic>/{name}/cmd_vel</topic><odom_topic>/{name}/odom</odom_topic><tf_topic>/{name}/tf</tf_topic>
        <frame_id>{name}/odom</frame_id><child_frame_id>{name}/base_link</child_frame_id>
        <odom_publish_frequency>30</odom_publish_frequency>
      </plugin>
    </model>"""


def build_pair_world(profile: str) -> str:
    """Return a complete two-robot world for one approved pair profile."""
    if profile not in PAIR_PROFILES:
        raise ValueError(f"unsupported pair profile: {profile}")
    world_name = f"pair_{profile}"
    return f"""<?xml version="1.0"?>
<sdf version="1.9">
  <world name="{world_name}">
    <physics name="pair_physics" type="ignored"><max_step_size>0.005</max_step_size><real_time_factor>1.0</real_time_factor></physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors"><render_engine>ogre2</render_engine></plugin>
    <gravity>0 0 -9.81</gravity>
    <scene><ambient>0.45 0.45 0.45 1</ambient><background>0.12 0.14 0.18 1</background><shadows>false</shadows></scene>
    <light name="warehouse_light" type="directional"><pose>0 0 12 0 0 0</pose><cast_shadows>false</cast_shadows><diffuse>0.85 0.85 0.85 1</diffuse><specular>0.1 0.1 0.1 1</specular><direction>-0.4 0.2 -0.9</direction></light>
    <model name="warehouse_floor"><static>true</static><pose>5 0 -0.05 0 0 0</pose><link name="link"><collision name="collision"><geometry><box><size>30 20 0.1</size></box></geometry></collision><visual name="visual"><geometry><box><size>30 20 0.1</size></box></geometry><material><ambient>0.42 0.44 0.46 1</ambient><diffuse>0.42 0.44 0.46 1</diffuse></material></visual></link></model>
    {_robot("leader", 2.0, camera=False, target=True)}
    {_robot("follower_1", 0.0, camera=True, target=True)}
  </world>
</sdf>
"""


def render_pair_world(profile: str, output_dir: Path) -> Path:
    """Write a content-addressed pair world and return its path."""
    text = build_pair_world(profile)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"pair_{profile}-{digest}.sdf"
    path.write_text(text, encoding="utf-8")
    return path


def build_chain_world(profile: str, follower_count: int) -> str:
    """Return a pair-derived world with two or three followers."""
    if profile not in PAIR_PROFILES:
        raise ValueError(f"unsupported chain profile: {profile}")
    if follower_count not in {2, 3}:
        raise ValueError("follower_count must be 2 or 3")
    text = build_pair_world(profile)
    text = text.replace(
        f'<world name="pair_{profile}">',
        f'<world name="chain_{follower_count}_{profile}">',
        1,
    )
    additions = "".join(
        _robot(
            f"follower_{index}",
            2.0 - 2.0 * index,
            camera=True,
            target=True,
        )
        for index in range(2, follower_count + 1)
    )
    return text.replace("  </world>", f"{additions}\n  </world>", 1)


def render_chain_world(profile: str, follower_count: int, output_dir: Path) -> Path:
    """Write a content-addressed incremental-chain world."""
    text = build_chain_world(profile, follower_count)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"chain_{follower_count}_{profile}-{digest}.sdf"
    path.write_text(text, encoding="utf-8")
    return path


def build_disturbance_world(scenario: str, follower_count: int) -> str:
    """Return the approved pair or three-follower Gate 5 world."""
    if scenario not in DISTURBANCE_SCENARIOS:
        raise ValueError(f"unsupported disturbance scenario: {scenario}")
    if follower_count not in {1, 3}:
        raise ValueError("disturbance follower_count must be 1 or 3")
    if follower_count == 1:
        text = build_pair_world("straight")
        old_name = "pair_straight"
    else:
        text = build_chain_world("straight", follower_count)
        old_name = f"chain_{follower_count}_straight"
    return text.replace(
        f'<world name="{old_name}">',
        f'<world name="disturbance_{follower_count}_{scenario}">',
        1,
    )


def render_disturbance_world(scenario: str, follower_count: int, output_dir: Path) -> Path:
    """Write a content-addressed Gate 5 world."""
    text = build_disturbance_world(scenario, follower_count)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"disturbance_{follower_count}_{scenario}-{digest}.sdf"
    path.write_text(text, encoding="utf-8")
    return path
