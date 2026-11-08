"""Gemelo digital: endpoint TCP para Unity + controlador del Kinova Gen3.

  ros2 launch kinova_mov kinova_unity.launch.py robot_ip:=192.168.1.10 ros_ip:=0.0.0.0 tcp_port:=10000
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    robot_ip = LaunchConfiguration("robot_ip")
    ros_ip = LaunchConfiguration("ros_ip")
    tcp_port = LaunchConfiguration("tcp_port")

    return LaunchDescription([
        DeclareLaunchArgument("robot_ip", default_value="192.168.1.10",
                              description="IP del Kinova Gen3"),
        DeclareLaunchArgument("ros_ip", default_value="0.0.0.0",
                              description="IP donde escucha ros_tcp_endpoint"),
        DeclareLaunchArgument("tcp_port", default_value="10000",
                              description="Puerto TCP de ros_tcp_endpoint (ROS Settings de Unity)"),
        Node(
            package="ros_tcp_endpoint",
            executable="default_server_endpoint",
            parameters=[{
                "ROS_IP": ros_ip,
                "ROS_TCP_PORT": ParameterValue(tcp_port, value_type=int),
            }],
            output="screen",
        ),
        Node(
            package="kinova_mov",
            executable="kinova_controller",
            parameters=[{"robot_ip": robot_ip}],
            output="screen",
        ),
    ])
