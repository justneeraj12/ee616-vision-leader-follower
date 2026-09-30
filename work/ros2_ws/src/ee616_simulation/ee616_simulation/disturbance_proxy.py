"""Deterministic camera and actuator disturbance proxy for Gate 5."""

from __future__ import annotations

import copy

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import String


DISTURBANCE_SCENARIOS = {
    "sharp_turn",
    "short_occlusion",
    "long_occlusion",
    "leader_stop",
    "actuator_bias",
    "combined",
}


def scheduled_event(scenario: str, elapsed_s: float, schedule_delay_s: float = 0.0) -> str:
    """Return the fixed event active at a simulation-relative time."""
    elapsed_s -= schedule_delay_s
    if scenario == "short_occlusion" and 9.0 <= elapsed_s < 9.5:
        return "SHORT_OCCLUSION"
    if scenario == "long_occlusion" and 9.0 <= elapsed_s < 10.3:
        return "LONG_OCCLUSION"
    if scenario == "actuator_bias" and 9.0 <= elapsed_s < 9.5:
        return "ACTUATOR_BIAS"
    if scenario == "combined":
        if 9.0 <= elapsed_s < 9.5:
            return "SHORT_OCCLUSION"
        if 12.0 <= elapsed_s < 13.3:
            return "LONG_OCCLUSION"
        if 34.0 <= elapsed_s < 34.5:
            return "ACTUATOR_BIAS"
    return "NONE"


def disturbed_command(
    linear_mps: float,
    angular_rps: float,
    event: str,
    *,
    angular_bias_rps: float = 0.15,
    max_linear_mps: float = 0.6,
    max_angular_rps: float = 0.8,
) -> tuple[float, float]:
    """Apply and clamp the approved bounded actuator disturbance."""
    angular = angular_rps + (angular_bias_rps if event == "ACTUATOR_BIAS" else 0.0)
    return (
        max(0.0, min(max_linear_mps, linear_mps)),
        max(-max_angular_rps, min(max_angular_rps, angular)),
    )


class DisturbanceProxyNode(Node):
    """Blank RGB frames or bias commands on a fixed schedule without truth input."""

    def __init__(self) -> None:
        super().__init__("disturbance_proxy")
        self.declare_parameter("scenario", "short_occlusion")
        self.declare_parameter("apply_disturbance", True)
        self.declare_parameter("publish_event", True)
        self.declare_parameter("input_image_topic", "camera/image")
        self.declare_parameter("output_image_topic", "camera/disturbed")
        self.declare_parameter("input_command_topic", "controller_cmd_vel")
        self.declare_parameter("output_command_topic", "cmd_vel")
        self.declare_parameter("event_topic", "/experiment/event")
        self.declare_parameter("angular_bias_rps", 0.15)
        self.declare_parameter("max_linear_mps", 0.6)
        self.declare_parameter("max_angular_rps", 0.8)
        self.declare_parameter("schedule_delay_s", 0.0)
        self.scenario = str(self.get_parameter("scenario").value)
        if self.scenario not in DISTURBANCE_SCENARIOS:
            raise ValueError(f"unsupported disturbance scenario: {self.scenario}")
        self.apply_disturbance = bool(self.get_parameter("apply_disturbance").value)
        self.publish_event = bool(self.get_parameter("publish_event").value)
        self.angular_bias_rps = float(self.get_parameter("angular_bias_rps").value)
        self.max_linear_mps = float(self.get_parameter("max_linear_mps").value)
        self.max_angular_rps = float(self.get_parameter("max_angular_rps").value)
        self.schedule_delay_s = float(self.get_parameter("schedule_delay_s").value)
        self.start_s: float | None = None
        self.image_publisher = self.create_publisher(
            Image, str(self.get_parameter("output_image_topic").value), qos_profile_sensor_data
        )
        self.command_publisher = self.create_publisher(
            Twist, str(self.get_parameter("output_command_topic").value), 10
        )
        self.event_publisher = self.create_publisher(
            String, str(self.get_parameter("event_topic").value), 10
        )
        self.create_subscription(
            Image,
            str(self.get_parameter("input_image_topic").value),
            self._image,
            qos_profile_sensor_data,
        )
        self.create_subscription(
            Twist,
            str(self.get_parameter("input_command_topic").value),
            self._command,
            10,
        )
        self.timer = self.create_timer(0.05, self._publish_event)

    def _elapsed(self) -> float:
        now_s = self.get_clock().now().nanoseconds * 1.0e-9
        if self.start_s is None:
            self.start_s = now_s
        return max(0.0, now_s - self.start_s)

    def _event(self) -> str:
        if not self.apply_disturbance:
            return "NONE"
        return scheduled_event(self.scenario, self._elapsed(), self.schedule_delay_s)

    def _image(self, message: Image) -> None:
        event = self._event()
        if event not in {"SHORT_OCCLUSION", "LONG_OCCLUSION"}:
            self.image_publisher.publish(message)
            return
        blank = copy.deepcopy(message)
        blank.data = bytes(len(message.data))
        self.image_publisher.publish(blank)

    def _command(self, message: Twist) -> None:
        linear, angular = disturbed_command(
            float(message.linear.x),
            float(message.angular.z),
            self._event(),
            angular_bias_rps=self.angular_bias_rps,
            max_linear_mps=self.max_linear_mps,
            max_angular_rps=self.max_angular_rps,
        )
        output = Twist()
        output.linear.x = linear
        output.angular.z = angular
        self.command_publisher.publish(output)

    def _publish_event(self) -> None:
        if not self.publish_event:
            return
        message = String()
        message.data = self._event()
        self.event_publisher.publish(message)

    def destroy_node(self):
        if rclpy.ok():
            self.command_publisher.publish(Twist())
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = DisturbanceProxyNode()
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
