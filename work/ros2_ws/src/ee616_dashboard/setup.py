from glob import glob

from setuptools import find_packages, setup


package_name = "ee616_dashboard"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/web", glob("web/*")),
    ],
    install_requires=["setuptools"],
    tests_require=["pytest"],
    zip_safe=True,
    maintainer="Neeraj Kumar Kanchani",
    maintainer_email="justneeraj12@users.noreply.github.com",
    description="Local experiment selection and read-only telemetry dashboard.",
    license="AGPL-3.0-only",
    entry_points={
        "console_scripts": [
            "experiment_console = "
            "ee616_dashboard.experiment_console:main",
        ],
    },
)
