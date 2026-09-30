import ast
from pathlib import Path

import ee616_control.control_core as control_core


def test_control_package_has_no_ground_truth_dependency():
    forbidden = {"gazebo_msgs", "ros_gz_interfaces", "ee616_evaluation", "subprocess"}
    package_root = Path(control_core.__file__).parent
    for source_path in package_root.glob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imported_roots = set()
        for item in ast.walk(tree):
            if isinstance(item, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in item.names)
            elif isinstance(item, ast.ImportFrom) and item.module:
                imported_roots.add(item.module.split(".")[0])
        assert imported_roots.isdisjoint(forbidden), source_path.name


def test_follower_node_inputs_are_measurement_and_local_odometry_only():
    source = (Path(control_core.__file__).parent / "follower_node.py").read_text(
        encoding="utf-8"
    )
    assert source.count("create_subscription(") == 2
    assert "Vector3Stamped," in source
    assert "Odometry," in source
