"""Conversión de ángulos de Kortex (grados) a sensor_msgs/JointState (radianes).

Sin dependencias de kortex_api para poder probarlo sin el robot.
"""
import math
from typing import Sequence

from builtin_interfaces.msg import Time
from sensor_msgs.msg import JointState


def make_joint_state(degrees: Sequence[float], stamp: Time) -> JointState:
    """Un JointState con joint_1..joint_N (N = len(degrees)) y posiciones en rad."""
    js = JointState()
    js.header.stamp = stamp
    js.name = [f"joint_{i + 1}" for i in range(len(degrees))]
    js.position = [math.radians(d) for d in degrees]
    return js
