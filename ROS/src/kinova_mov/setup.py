from glob import glob

from setuptools import find_packages, setup

package_name = "kinova_mov"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Juan Gómez",
    maintainer_email="juangomez154879@gmail.com",
    description="Control del Kinova Gen3 por Kortex API para el gemelo digital en Unity.",
    license="BSD-3-Clause",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "kinova_controller = kinova_mov.kinova_controller:main",
        ],
    },
)
