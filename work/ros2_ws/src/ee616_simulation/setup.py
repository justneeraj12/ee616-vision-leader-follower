from glob import glob
from setuptools import find_packages, setup


package_name = "ee616_simulation"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/config", glob("config/*.yaml")),
        (f"share/{package_name}/launch", glob("launch/*.launch.py")),
        (f"share/{package_name}/worlds", glob("worlds/*.sdf")),
    ],
    install_requires=["setuptools"],
    tests_require=["pytest"],
    zip_safe=True,
    maintainer="Neeraj Kumar Kanchani",
    maintainer_email="justneeraj12@users.noreply.github.com",
    description="Gazebo Harmonic simulation assets for the EE 616 project.",
    license="Proprietary",
)
