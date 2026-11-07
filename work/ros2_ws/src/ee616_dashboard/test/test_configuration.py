from pathlib import Path

from ee616_dashboard.configuration import (
    ExperimentConfig,
    MAP_PROFILES,
    ROUTE_PROFILES,
    SCENARIO_PROFILES,
)
import pytest


@pytest.mark.parametrize("follower_count", [1, 2, 3])
@pytest.mark.parametrize("route_profile", sorted(ROUTE_PROFILES))
@pytest.mark.parametrize("map_profile", sorted(MAP_PROFILES))
@pytest.mark.parametrize("scenario_profile", sorted(SCENARIO_PROFILES))
def test_valid_profiles_make_injection_safe_commands(
    follower_count, route_profile, map_profile, scenario_profile
):
    config = ExperimentConfig.from_mapping({
        "follower_count": follower_count,
        "route_profile": route_profile,
        "map_profile": map_profile,
        "scenario_profile": scenario_profile,
        "gui": True,
    })
    command = config.launch_command(Path("/tmp/ee616-result"))
    assert command[:4] == [
        "ros2", "launch", "ee616_evaluation", "warehouse_nav_mission.launch.py"
    ]
    assert f"follower_count:={follower_count}" in command
    assert f"route_profile:={route_profile}" in command
    assert f"map_profile:={map_profile}" in command
    assert "gui:=true" in command


@pytest.mark.parametrize(
    "values",
    [
        {"follower_count": 0},
        {"follower_count": 4},
        {"route_profile": "../../outside"},
        {"map_profile": "../../outside"},
        {"scenario_profile": "../../outside"},
        {"gui": "true"},
    ],
)
def test_invalid_profiles_are_rejected(values):
    with pytest.raises(ValueError):
        ExperimentConfig.from_mapping(values)


def test_default_profile_is_the_repeated_pair_first_configuration():
    config = ExperimentConfig.from_mapping({})
    assert config.route_profile == "wide"
    assert config.map_profile == "sparse"
    assert config.scenario_profile == "nominal"
