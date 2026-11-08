#!/usr/bin/env python3
"""Publicador de prueba: /joint_states con una onda seno a 60 Hz (sin robot)."""
import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

JOINT_NAMES = [f"joint_{i}" for i in range(1, 7)]


class FakeJointStates(Node):
    def __init__(self):
        super().__init__("fake_joint_states")
        self.pub = self.create_publisher(JointState, "/joint_states", 10)
        self.angle = 0.0
        self.timer = self.create_timer(1.0 / 60.0, self.tick)

    def tick(self):
        js = JointState()
        js.header.stamp = self.get_clock().now().to_msg()
        js.name = JOINT_NAMES
        js.position = [math.sin(self.angle + i) * 0.5 for i in range(len(JOINT_NAMES))]
        self.pub.publish(js)
        self.angle += 0.05


def main():
    rclpy.init()
    node = FakeJointStates()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
