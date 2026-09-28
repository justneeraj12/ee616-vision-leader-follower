from pathlib import Path


def test_camera_smoke_world_exists():
    package_root = Path(__file__).parents[1]
    assert (package_root / "worlds" / "camera_smoke.sdf").is_file()


def test_warehouse_playground_assets_exist():
    package_root = Path(__file__).parents[1]
    assert (package_root / "worlds" / "warehouse_playground.sdf").is_file()
    assert (
        package_root / "launch" / "warehouse_playground.launch.py"
    ).is_file()
