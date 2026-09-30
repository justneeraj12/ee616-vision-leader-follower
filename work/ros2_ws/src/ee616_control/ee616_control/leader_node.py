"""Deterministic leader route used only for the pair integration gate."""

from __future__ import annotations

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class LeaderRouteNode(Node):
    """Publish a bounded straight or gradual-turn velocity profile."""

    def __init__(self) -> None:
        super().__init__("leader_route")
        self.declare_parameter("profile", "straight")
        self.declare_parameter("command_topic", "cmd_vel")
        self.declare_parameter("state_topic", "route/state")
        self.declare_parameter("linear_mps", 0.35)
        self.declare_parameter("turn_angular_rps", 0.12)
        self.declare_parameter("settle_s", 4.0)
        self.profile = str(self.get_parameter("profile").value)
        if self.profile not in {
            "straight", "turn", "sharp_turn", "short_occlusion",
            "long_occlusion", "leader_stop", "actuator_bias", "combined",
        }:
            raise ValueError("unsupported leader route profile")
        self.linear_mps = float(self.get_parameter("linear_mps").value)
        self.turn_angular_rps = float(self.get_parameter("turn_angular_rps").value)
        self.settle_s = float(self.get_parameter("settle_s").value)
        self.started_s = self.get_clock().now().nanoseconds * 1.0e-9
        self.command_publisher = self.create_publisher(
            Twist, str(self.get_parameter("command_topic").value), 10
        )
        self.state_publisher = self.create_publisher(
            String, str(self.get_parameter("state_topic").value), 10
        )
        self.timer = self.create_timer(0.05, self._tick)

    def _profile_command(self, elapsed_s: float) -> tuple[float, float, str]:
        if elapsed_s < self.settle_s:
            return 0.0, 0.0, "SETTLE"
        route_s = elapsed_s - self.settle_s
        if self.profile == "straight":
            if route_s < 16.0:
                return self.linear_mps, 0.0, "STRAIGHT"
            return 0.0, 0.0, "COMPLETE"
        if self.profile in {"short_occlusion", "long_occlusion", "actuator_bias"}:
            if route_s < 16.0:
                return self.linear_mps, 0.0, "STRAIGHT"
            return 0.0, 0.0, "COMPLETE"
        if self.profile == "sharp_turn":
            if route_s < 4.0:
                return self.linear_mps, 0.0, "STRAIGHT_1"
            if route_s < 10.0:
                return self.linear_mps, 0.18, "TURN_HARD"
            if route_s < 16.0:
                return self.linear_mps, 0.0, "STRAIGHT_2"
            return 0.0, 0.0, "COMPLETE"
        if self.profile == "leader_stop":
            if route_s < 5.0:
                return self.linear_mps, 0.0, "STRAIGHT_1"
            if route_s < 9.0:
                return 0.0, 0.0, "STOPPED"
            if route_s < 15.0:
                return self.linear_mps, 0.0, "STRAIGHT_2"
            return 0.0, 0.0, "COMPLETE"
        if self.profile == "combined":
            elapsed_s = route_s + 4.0
            if elapsed_s < 14.0:
                return self.linear_mps, 0.0, "STRAIGHT_1"
            if elapsed_s < 20.0:
                return self.linear_mps, 0.18, "TURN_HARD"
            if elapsed_s < 22.0:
                return self.linear_mps, 0.0, "STRAIGHT_2"
            if elapsed_s < 26.0:
                return 0.0, 0.0, "STOPPED"
            if elapsed_s < 42.0:
                return self.linear_mps, 0.0, "STRAIGHT_3"
            return 0.0, 0.0, "COMPLETE"
        if route_s < 5.0:
            return self.linear_mps, 0.0, "STRAIGHT_1"
        if route_s < 13.0:
            return self.linear_mps, self.turn_angular_rps, "TURN"
        if route_s < 18.0:
            return self.linear_mps, 0.0, "STRAIGHT_2"
        return 0.0, 0.0, "COMPLETE"

    def _tick(self) -> None:
        now_s = self.get_clock().now().nanoseconds * 1.0e-9
        linear, angular, route_state = self._profile_command(now_s - self.started_s)
        command = Twist()
        command.linear.x = linear
        command.angular.z = angular
        self.command_publisher.publish(command)
        state = String()
        state.data = route_state
        self.state_publisher.publish(state)

    def destroy_node(self):
        if rclpy.ok():
            self.command_publisher.publish(Twist())
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = LeaderRouteNode()
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
