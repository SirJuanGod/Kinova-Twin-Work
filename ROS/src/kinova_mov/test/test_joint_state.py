import math

import pytest
from builtin_interfaces.msg import Time
from kinova_mov.joint_state import make_joint_state


def test_make_joint_state_converts_degrees_to_radians():
    js = make_joint_state([0.0, 90.0, 180.0, 360.0, -90.0, 45.0], Time(sec=3))
    assert js.name == [f"joint_{i}" for i in range(1, 7)]
    # rclpy guarda position como array('d'): se compara como lista
    assert list(js.position) == pytest.approx(
        [0.0, math.pi / 2, math.pi, 2 * math.pi, -math.pi / 2, math.pi / 4])
    assert js.header.stamp.sec == 3


def test_make_joint_state_uses_reported_count():
    js = make_joint_state([10.0] * 7, Time())
    assert js.name[-1] == "joint_7" and len(js.position) == 7
