"""ROS wrapper for the deterministic warehouse cargo mission."""

from __future__ import annotations

import json

from ee616_control.warehouse_mission import WarehouseMissionPlan, cargo_position
from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64, String


class WarehouseMissionNode(Node):
    """Command the route-owning leader and the presentation cargo lifts."""

    def __init__(self) -> None:
        super().__init__("warehouse_mission")
        self.declare_parameter("follower_count", 3)
        self.declare_parameter("startup_s", 10.0)
        self.declare_parameter("command_topic", "cmd_vel")
        self.declare_parameter("route_state_topic", "route/state")
        self.follower_count = int(self.get_parameter("follower_count").value)
        startup_s = float(self.get_parameter("startup_s").value)
        self.plan = WarehouseMissionPlan(
            self.follower_count, startup_s=startup_s
        )
        self.started_s = self.get_clock().now().nanoseconds * 1.0e-9
        self.command_publisher = self.create_publisher(
            Twist, str(self.get_parameter("command_topic").value), 10
        )
        self.route_state_publisher = self.create_publisher(
            String, str(self.get_parameter("route_state_topic").value), 10
        )
        self.mission_state_publisher = self.create_publisher(
            String, "/warehouse_mission/state", 10
        )
        self.cargo_state_publisher = self.create_publisher(
            String, "/warehouse_mission/cargo_state", 10
        )
        self.cargo_publishers = {
            robot: self.create_publisher(
                Float64, f"/warehouse_mission/{robot}/cargo_position", 10
            )
            for robot in self.plan.robots
        }
        self.timer = self.create_timer(0.05, self._tick)

    def _tick(self) -> None:
        now_s = self.get_clock().now().nanoseconds * 1.0e-9
        output = self.plan.output(now_s - self.started_s)
        command = Twist()
        command.linear.x = output.linear_mps
        command.angular.z = output.angular_rps
        self.command_publisher.publish(command)

        state = String()
        state.data = output.state
        self.route_state_publisher.publish(state)
        self.mission_state_publisher.publish(state)

        cargo_state = String()
        cargo_state.data = json.dumps(output.cargo_loaded, sort_keys=True)
        self.cargo_state_publisher.publish(cargo_state)
        for robot, loaded in output.cargo_loaded.items():
            position = Float64()
            position.data = cargo_position(loaded)
            self.cargo_publishers[robot].publish(position)

    def destroy_node(self):
        if rclpy.ok():
            self.command_publisher.publish(Twist())
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = WarehouseMissionNode()
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
