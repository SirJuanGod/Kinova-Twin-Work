"""robot_state_publisher + RViz2 para el Kinova Gen3.

Args:
  fake:=true   lanza fake_joint_states.py (seno a 60 Hz) en vez de esperar al robot.
  rviz:=false  no abre RViz2.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory("kinova_gen3_description")
    with open(os.path.join(share, "urdf", "GEN3.urdf")) as f:
        robot_description = f.read()

    fake = LaunchConfiguration("fake")
    rviz = LaunchConfiguration("rviz")

    return LaunchDescription([
        DeclareLaunchArgument("fake", default_value="false",
                              description="Publicar /joint_states de prueba (seno)"),
        DeclareLaunchArgument("rviz", default_value="true",
                              description="Abrir RViz2"),
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[{"robot_description": robot_description}],
            output="screen",
        ),
        Node(
            package="kinova_gen3_description",
            executable="fake_joint_states.py",
            condition=IfCondition(fake),
            output="screen",
        ),
        Node(
            package="rviz2",
            executable="rviz2",
            arguments=["-d", os.path.join(share, "rviz", "gen3.rviz")],
            condition=IfCondition(rviz),
        ),
    ])
