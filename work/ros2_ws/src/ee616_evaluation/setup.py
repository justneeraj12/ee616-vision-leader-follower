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
        (f"share/{package_name}/config", glob("config/*.yaml")),
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
            "chain_gate_evaluator = "
            "ee616_evaluation.chain_gate_evaluator:main",
            "disturbance_gate_evaluator = "
            "ee616_evaluation.disturbance_gate_evaluator:main",
            "timing_gate_evaluator = "
            "ee616_evaluation.timing_gate_evaluator:main",
            "pair_gate_evaluator = "
            "ee616_evaluation.pair_gate_evaluator:main",
            "plot_chain_gate = "
            "ee616_evaluation.plot_chain_gate:main",
            "plot_disturbance_gate = "
            "ee616_evaluation.plot_disturbance_gate:main",
            "plot_pair_gate = "
            "ee616_evaluation.plot_pair_gate:main",
            "plot_timing_gate = "
            "ee616_evaluation.plot_timing_gate:main",
            "summarize_chain_gate = "
            "ee616_evaluation.summarize_chain_gate:main",
            "summarize_disturbance_gate = "
            "ee616_evaluation.summarize_disturbance_gate:main",
            "summarize_pair_gate = "
            "ee616_evaluation.summarize_pair_gate:main",
            "summarize_timing_gate = "
            "ee616_evaluation.summarize_timing_gate:main",
            "summarize_camera_gate = "
            "ee616_evaluation.summarize_camera_gate:main",
            "validate_yolo_dataset = "
            "ee616_evaluation.validate_yolo_dataset:main",
            "yolo_dataset_capture = "
            "ee616_evaluation.yolo_dataset_capture:main",
        ],
    },
)
