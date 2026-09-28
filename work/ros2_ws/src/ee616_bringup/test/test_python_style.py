from pathlib import Path


def test_launch_file_exists():
    package_root = Path(__file__).parents[1]
    assert (package_root / "launch" / "namespace_smoke.launch.py").is_file()
