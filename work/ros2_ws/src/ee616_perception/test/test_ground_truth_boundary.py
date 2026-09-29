import ast
from pathlib import Path

import ee616_perception.camera_measurement_node as node_module


def test_perception_node_has_no_ground_truth_dependency():
    source_path = Path(node_module.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_roots = set()
    for item in ast.walk(tree):
        if isinstance(item, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in item.names)
        elif isinstance(item, ast.ImportFrom) and item.module:
            imported_roots.add(item.module.split(".")[0])
    forbidden = {"gazebo_msgs", "ros_gz_interfaces", "ee616_evaluation"}
    assert imported_roots.isdisjoint(forbidden)


def test_perception_subscribes_only_to_image_messages():
    source = Path(node_module.__file__).read_text(encoding="utf-8")
    assert "create_subscription(\n            Image," in source
    assert source.count("create_subscription(") == 1
