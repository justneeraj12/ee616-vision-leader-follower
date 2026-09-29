from glob import glob

from setuptools import find_packages, setup


package_name = "ee616_evaluation"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    tests_require=["pytest"],
    zip_safe=True,
    maintainer="Neeraj Kumar Kanchani",
    maintainer_email="justneeraj12@users.noreply.github.com",
    description="Evaluation-only Gazebo ground-truth and metric tools.",
    license="AGPL-3.0-only",
    entry_points={
        "console_scripts": [
            "camera_gate_evaluator = "
            "ee616_evaluation.camera_gate_evaluator:main",
            "summarize_camera_gate = "
            "ee616_evaluation.summarize_camera_gate:main",
        ],
    },
)
