from collections import defaultdict
from glob import glob
from pathlib import Path

from setuptools import find_packages, setup


package_name = "ee616_simulation"


def install_tree(source_root):
    grouped = defaultdict(list)
    for path in sorted(Path(source_root).rglob("*")):
        if path.is_file():
            destination = f"share/{package_name}/{path.parent.as_posix()}"
            grouped[destination].append(str(path))
    return sorted(grouped.items())


setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/config", glob("config/*.yaml")),
        (f"share/{package_name}/launch", glob("launch/*.launch.py")),
        (f"share/{package_name}/scenarios", glob("scenarios/*.yaml")),
        (f"share/{package_name}/worlds", glob("worlds/*.sdf")),
    ]
    + install_tree("vendor"),
    install_requires=["setuptools", "PyYAML"],
    tests_require=["pytest"],
    zip_safe=True,
    maintainer="Neeraj Kumar Kanchani",
    maintainer_email="justneeraj12@users.noreply.github.com",
    description="Gazebo Harmonic simulation assets for the EE 616 project.",
    license="Proprietary",
    entry_points={
        "console_scripts": [
            "scenario_builder = ee616_simulation.scenario_builder:main",
        ],
    },
)
