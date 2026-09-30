import ast
from pathlib import Path

import ee616_perception.camera_measurement_node as node_module


def test_perception_node_has_no_ground_truth_dependency():
    forbidden = {"gazebo_msgs", "ros_gz_interfaces", "ee616_evaluation"}
    package_root = Path(node_module.__file__).parent
    for source_path in package_root.glob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imported_roots = set()
        for item in ast.walk(tree):
            if isinstance(item, ast.Import):
                imported_roots.update(
                    alias.name.split(".")[0] for alias in item.names
                )
            elif isinstance(item, ast.ImportFrom) and item.module:
                imported_roots.add(item.module.split(".")[0])
        assert imported_roots.isdisjoint(forbidden), source_path.name


def test_perception_subscribes_only_to_image_messages():
    package_root = Path(node_module.__file__).parent
    node_paths = [
        package_root / "camera_measurement_node.py",
        package_root / "yolo_measurement_node.py",
    ]
    for node_path in node_paths:
        source = node_path.read_text(encoding="utf-8")
        assert "create_subscription(\n            Image," in source
        assert source.count("create_subscription(") == 1
