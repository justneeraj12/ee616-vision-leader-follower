"""Validated experiment profiles used by the local dashboard."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


ROUTE_PROFILES = {
    "wide": {
        "label": "Wide route",
        "description": "Three goals with two principal aisle changes.",
        "waypoint_count": 3,
        "duration_s": 320.0,
        "evidence_status": (
            "Three repeated governed pair runs passed. Three chain runs "
            "stopped safely but did not complete after visual loss."
        ),
    },
    "standard": {
        "label": "Standard warehouse",
        "description": "The preserved four-goal mapped mission.",
        "waypoint_count": 4,
        "duration_s": 320.0,
        "evidence_status": (
            "The earlier frozen mapped mission passed. A revised governed "
            "pair run is retained as a failed diagnostic."
        ),
    },
    "turn_dense": {
        "label": "Turn-dense stress route",
        "description": (
            "Eight goals through all four horizontal aisles. This profile is "
            "intended to expose visual-chain limits, not guarantee completion."
        ),
        "waypoint_count": 8,
        "duration_s": 620.0,
        "evidence_status": (
            "Known pair failure after the second cross-aisle turn on 2026-11-07."
        ),
    },
}

MAP_PROFILES = {
    "standard": {
        "label": "Nine-shelf warehouse",
        "description": "Three rows with three shelf blocks per row.",
        "shelf_count": 9,
        "evidence_status": "Selectable diagnostic layout in the revised gate.",
    },
    "sparse": {
        "label": "Six-shelf flexible warehouse",
        "description": "A removable center bay creates wider internal openings.",
        "shelf_count": 6,
        "evidence_status": "Repeated pair mission and chain containment evidence.",
    },
}

SCENARIO_PROFILES = {
    "nominal": {
        "label": "Nominal mission",
        "description": "No injected leader-command fault.",
        "fault_mode": "none",
    },
    "leader_dropout": {
        "label": "Leader command-dropout recovery",
        "description": (
            "Injects a bounded three-second leader command dropout and verifies "
            "that the governor commands zero before the mission resumes."
        ),
        "fault_mode": "leader_cmd_dropout",
    },
}


@dataclass(frozen=True)
class ExperimentConfig:
    """One bounded dashboard launch request."""

    follower_count: int = 3
    route_profile: str = "wide"
    map_profile: str = "sparse"
    scenario_profile: str = "nominal"
    gui: bool = True

    @classmethod
    def from_mapping(cls, values: dict) -> "ExperimentConfig":
        """Build and validate a configuration from decoded JSON."""
        try:
            follower_count = int(values.get("follower_count", 3))
        except (TypeError, ValueError) as error:
            raise ValueError("follower_count must be an integer") from error
        route_profile = str(values.get("route_profile", "wide"))
        map_profile = str(values.get("map_profile", "sparse"))
        scenario_profile = str(values.get("scenario_profile", "nominal"))
        gui = values.get("gui", True)
        if not isinstance(gui, bool):
            raise ValueError("gui must be true or false")
        if follower_count not in {1, 2, 3}:
            raise ValueError("follower_count must be 1, 2, or 3")
        if route_profile not in ROUTE_PROFILES:
            choices = ", ".join(sorted(ROUTE_PROFILES))
            raise ValueError(f"route_profile must be one of: {choices}")
        if map_profile not in MAP_PROFILES:
            choices = ", ".join(sorted(MAP_PROFILES))
            raise ValueError(f"map_profile must be one of: {choices}")
        if scenario_profile not in SCENARIO_PROFILES:
            choices = ", ".join(sorted(SCENARIO_PROFILES))
            raise ValueError(f"scenario_profile must be one of: {choices}")
        return cls(
            follower_count,
            route_profile,
            map_profile,
            scenario_profile,
            gui,
        )

    @property
    def duration_s(self) -> float:
        return float(ROUTE_PROFILES[self.route_profile]["duration_s"])

    def as_dict(self) -> dict:
        return asdict(self)

    def launch_command(self, output_dir: Path) -> list[str]:
        """Return an injection-safe ROS launch command."""
        return [
            "ros2",
            "launch",
            "ee616_evaluation",
            "warehouse_nav_mission.launch.py",
            f"follower_count:={self.follower_count}",
            f"route_profile:={self.route_profile}",
            f"map_profile:={self.map_profile}",
            "fault_mode:="
            f"{SCENARIO_PROFILES[self.scenario_profile]['fault_mode']}",
            "require_fault_event:="
            f"{'true' if self.scenario_profile == 'leader_dropout' else 'false'}",
            "run_id:=run_01",
            f"output_dir:={output_dir}",
            f"duration_s:={self.duration_s}",
            f"gui:={'true' if self.gui else 'false'}",
            "render_engine:=ogre2",
            "detector_device:=0",
            "startup_s:=12.0",
        ]
