"""Nodo kinova_controller: puente entre ROS2 y el Kinova Gen3 por la Kortex API.

Port a rclpy de kinova_mov/scripts/pruebas_api.py (ROS1).

- Publica /joint_states (sensor_msgs/JointState, rad) y kinova_current
  (std_msgs/String) a `publish_rate` Hz.
- Escucha /controller (geometry_msgs/PoseStamped): calcula la IK en el robot
  (posición del mensaje, orientación actual) y mueve el brazo.

El timer y la suscripción van en grupos de callback distintos dentro de un
MultiThreadedExecutor, así /joint_states sigue publicándose mientras el brazo
se mueve.
"""
import socket
import sys
import threading

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String

from kortex_api.autogen.client_stubs.BaseClientRpc import BaseClient
from kortex_api.autogen.messages import Base_pb2
from kortex_api.Exceptions.KServerException import KServerException

from kinova_mov.joint_state import make_joint_state
from kinova_mov.utilities import DeviceConnection

TIMEOUT_DURATION = 15  # s, espera máxima de una acción Kortex
CONNECT_TIMEOUT = 5  # s; TCPTransport de Kortex no tiene timeout (el kernel tarda ~2 min)


def check_for_end_or_abort(e):
    """Closure que activa `e` cuando llega una notificación END o ABORT."""
    def check(notification, e=e):
        print("EVENT : " + Base_pb2.ActionEvent.Name(notification.action_event))
        if notification.action_event in (Base_pb2.ACTION_END, Base_pb2.ACTION_ABORT):
            e.set()
    return check


class KinovaController(Node):
    def __init__(self):
        super().__init__("kinova_controller")
        self.declare_parameter("robot_ip", "192.168.1.10")
        self.declare_parameter("username", "admin")
        self.declare_parameter("password", "admin")
        self.declare_parameter("publish_rate", 10.0)
        self.declare_parameter("home_action", "Home")
        self.base = None

    def param(self, name):
        return self.get_parameter(name).value

    def start(self, base: BaseClient) -> None:
        self.base = base
        self.move_to_home()

        self.state_pub = self.create_publisher(String, "kinova_current", 10)
        self.joint_pub = self.create_publisher(JointState, "/joint_states", 10)

        self.timer = self.create_timer(
            1.0 / float(self.param("publish_rate")), self.publish_state,
            callback_group=MutuallyExclusiveCallbackGroup())
        self.pose_sub = self.create_subscription(
            PoseStamped, "/controller", self.on_pose, 10,
            callback_group=MutuallyExclusiveCallbackGroup())

    def _wait_action(self, start_action) -> bool:
        """Ejecuta `start_action()` y espera END/ABORT hasta TIMEOUT_DURATION."""
        e = threading.Event()
        handle = self.base.OnNotificationActionTopic(
            check_for_end_or_abort(e), Base_pb2.NotificationOptions())
        try:
            start_action()
            return e.wait(TIMEOUT_DURATION)
        finally:
            self.base.Unsubscribe(handle)

    def move_to_home(self) -> bool:
        # El brazo tiene que estar en Single Level Servoing
        servo_mode = Base_pb2.ServoingModeInformation()
        servo_mode.servoing_mode = Base_pb2.SINGLE_LEVEL_SERVOING
        self.base.SetServoingMode(servo_mode)

        home = self.param("home_action")
        self.get_logger().info(f"Moviendo el brazo a la acción '{home}'")
        action_type = Base_pb2.RequestedActionType()
        action_type.action_type = Base_pb2.REACH_JOINT_ANGLES
        action_list = self.base.ReadAllActions(action_type)
        handle = next((a.handle for a in action_list.action_list if a.name == home), None)
        if handle is None:
            self.get_logger().error(f"No existe la acción '{home}' en el robot")
            return False

        finished = self._wait_action(lambda: self.base.ExecuteActionFromReference(handle))
        if finished:
            self.get_logger().info("Posición segura alcanzada")
        else:
            self.get_logger().warn("Timeout esperando la acción de Home")
        return finished

    def publish_state(self) -> None:
        try:
            joint_angles = self.base.GetMeasuredJointAngles()
            pose = self.base.ComputeForwardKinematics(joint_angles)
        except Exception as ex:
            self.get_logger().error(f"No se pueden leer los ángulos del brazo: {ex}")
            return

        self.state_pub.publish(String(data=(
            f"Arm actual pos: x: {pose.x:.3f}, y: {pose.y:.3f}, z: {pose.z:.3f}, "
            f"theta_x: {pose.theta_x:.2f}, theta_y: {pose.theta_y:.2f}, theta_z: {pose.theta_z:.2f}")))
        self.joint_pub.publish(make_joint_state(
            [ja.value for ja in joint_angles.joint_angles],
            self.get_clock().now().to_msg()))

    def on_pose(self, msg: PoseStamped) -> None:
        p = msg.pose.position
        self.get_logger().info(f"Pose recibida en /controller: x={p.x:.3f} y={p.y:.3f} z={p.z:.3f}")
        try:
            input_joint_angles = self.base.GetMeasuredJointAngles()
            pose = self.base.ComputeForwardKinematics(input_joint_angles)
        except KServerException as ex:
            self.get_logger().error(f"No se puede obtener la pose actual del robot: {ex}")
            return

        ik = Base_pb2.IKData()
        ik.cartesian_pose.x = p.x
        ik.cartesian_pose.y = p.y
        ik.cartesian_pose.z = p.z
        # Se mantiene la orientación actual del efector
        ik.cartesian_pose.theta_x = pose.theta_x
        ik.cartesian_pose.theta_y = pose.theta_y
        ik.cartesian_pose.theta_z = pose.theta_z
        for ja in input_joint_angles.joint_angles:
            ik.guess.joint_angles.add().value = ja.value

        try:
            computed = self.base.ComputeInverseKinematics(ik)
        except KServerException as ex:
            self.get_logger().error(f"La IK no tiene solución para esa pose: {ex}")
            return

        self.send_joint_angles(computed)

    def send_joint_angles(self, joint_angles) -> None:
        command = Base_pb2.Action()
        command.name = "move_to_ik_result"
        command.application_data = ""
        for i, angle in enumerate(joint_angles.joint_angles):
            joint = command.reach_joint_angles.joint_angles.joint_angles.add()
            joint.joint_identifier = i
            joint.value = angle.value

        try:
            finished = self._wait_action(lambda: self.base.ExecuteAction(command))
        except KServerException as ex:
            self.get_logger().error(f"El robot rechazó el movimiento: {ex}")
            return
        if finished:
            self.get_logger().info("Movimiento por IK ejecutado.")
        else:
            self.get_logger().warn("Timeout o fallo ejecutando el movimiento por IK.")


def main(args=None):
    rclpy.init(args=args)
    node = KinovaController()
    ip = node.param("robot_ip")
    exit_code = 0
    try:
        # Falla rápido si el robot no responde, antes de abrir la sesión Kortex
        socket.create_connection((ip, DeviceConnection.TCP_PORT), timeout=CONNECT_TIMEOUT).close()
        with DeviceConnection(ip, port=DeviceConnection.TCP_PORT,
                              credentials=(node.param("username"), node.param("password"))) as router:
            node.start(BaseClient(router))
            node.get_logger().info(f"Conectado al robot en {ip}")
            executor = MultiThreadedExecutor()
            executor.add_node(node)
            executor.spin()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except Exception as ex:
        node.get_logger().error(f"No se pudo conectar al robot en {ip}: {ex}")
        exit_code = 1
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
