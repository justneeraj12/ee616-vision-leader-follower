"""ROS wrapper for the one-follower estimator, controller, and supervisor."""

from __future__ import annotations

import math

from ee616_control.control_core import FollowerSupervisor
from geometry_msgs.msg import Twist, Vector3Stamped
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import String


class FollowerControllerNode(Node):
    """Use camera measurements and local odometry to command one follower."""

    def __init__(self) -> None:
        super().__init__("follower_controller")
        defaults = {
            "desired_range_m": 1.5,
            "max_linear_mps": 0.6,
            "max_angular_rps": 0.8,
            "track_timeout_s": 0.2,
            "predict_timeout_s": 0.75,
            "range_gain": 0.85,
            "range_rate_gain": 0.85,
            "bearing_gain": 1.8,
            "bearing_rate_gain": 0.2,
            "predict_speed_scale": 0.55,
            "control_rate_hz": 20.0,
        }
        for name, value in defaults.items():
            self.declare_parameter(name, value)
        self.declare_parameter("measurement_topic", "measurement/relative")
        self.declare_parameter("odometry_topic", "odom")
        self.declare_parameter("command_topic", "cmd_vel")
        self.declare_parameter("state_topic", "control/state")
        self.declare_parameter("estimate_topic", "control/estimate")
        values = {name: float(self.get_parameter(name).value) for name in defaults}
        control_rate_hz = values.pop("control_rate_hz")
        self.supervisor = FollowerSupervisor(**values)
        self.forward_speed = 0.0
        self.yaw_rate = 0.0
        self.command_publisher = self.create_publisher(
            Twist, str(self.get_parameter("command_topic").value), 10
        )
        self.state_publisher = self.create_publisher(
            String, str(self.get_parameter("state_topic").value), 10
        )
        self.estimate_publisher = self.create_publisher(
            Vector3Stamped, str(self.get_parameter("estimate_topic").value), 10
        )
        self.create_subscription(
            Vector3Stamped,
            str(self.get_parameter("measurement_topic").value),
            self._measurement,
            10,
        )
        self.create_subscription(
            Odometry,
            str(self.get_parameter("odometry_topic").value),
            self._odometry,
            qos_profile_sensor_data,
        )
        self.timer = self.create_timer(1.0 / control_rate_hz, self._control)

    def _now(self) -> float:
        return self.get_clock().now().nanoseconds * 1.0e-9

    def _odometry(self, message: Odometry) -> None:
        self.forward_speed = float(message.twist.twist.linear.x)
        self.yaw_rate = float(message.twist.twist.angular.z)

    def _measurement(self, message: Vector3Stamped) -> None:
        if message.vector.z < 0.5:
            return
        self.supervisor.accept_measurement(
            float(message.vector.x),
            float(message.vector.y),
            self._now(),
            self.forward_speed,
            self.yaw_rate,
        )

    def _control(self) -> None:
        output = self.supervisor.step(self._now(), self.forward_speed, self.yaw_rate)
        command = Twist()
        command.linear.x = output.linear_mps
        command.angular.z = output.angular_rps
        self.command_publisher.publish(command)
        state = String()
        state.data = output.state
        self.state_publisher.publish(state)
        estimate = Vector3Stamped()
        estimate.header.stamp = self.get_clock().now().to_msg()
        estimate.header.frame_id = "follower_1/camera"
        estimate.vector.x = output.range_m
        estimate.vector.y = output.bearing_rad
        estimate.vector.z = output.measurement_age_s if math.isfinite(output.measurement_age_s) else -1.0
        self.estimate_publisher.publish(estimate)

    def destroy_node(self):
        if rclpy.ok():
            self.command_publisher.publish(Twist())
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = FollowerControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except RuntimeError:
        if rclpy.ok():
            raise
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
