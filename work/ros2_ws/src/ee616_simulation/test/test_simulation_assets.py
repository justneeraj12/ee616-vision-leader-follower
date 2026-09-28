from pathlib import Path


def test_camera_smoke_world_exists():
    package_root = Path(__file__).parents[1]
    assert (package_root / "worlds" / "camera_smoke.sdf").is_file()
