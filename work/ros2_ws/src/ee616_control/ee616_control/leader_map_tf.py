"""Anchor wheel odometry to the known warehouse start without ground truth."""

from __future__ import annotations

import math

from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node
from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster


LIDAR_HEIGHT_M = 0.90


def _yaw_from_quaternion(quaternion) -> float:
    siny = 2.0 * (
        quaternion.w * quaternion.z + quaternion.x * quaternion.y
    )
    cosy = 1.0 - 2.0 * (
        quaternion.y * quaternion.y + quaternion.z * quaternion.z
    )
    return math.atan2(siny, cosy)


class LeaderMapTf(Node):
    """Publish leader odometry TF while AMCL owns map localization."""

    def __init__(self) -> None:
        super().__init__("leader_map_tf")
        self.declare_parameter("initial_map_x_m", -10.0)
        self.declare_parameter("initial_map_y_m", -6.0)
        self.declare_parameter("initial_map_yaw_rad", 0.0)
        self.declare_parameter("publish_map_anchor", False)
        self.map_x = float(self.get_parameter("initial_map_x_m").value)
        self.map_y = float(self.get_parameter("initial_map_y_m").value)
        self.map_yaw = float(self.get_parameter("initial_map_yaw_rad").value)
        self.publish_map_anchor = bool(
            self.get_parameter("publish_map_anchor").value
        )
        self.map_to_odom: tuple[float, float, float] | None = None
        self.broadcaster = TransformBroadcaster(self)
        self.static_broadcaster = StaticTransformBroadcaster(self)
        lidar_transform = TransformStamped()
        lidar_transform.header.stamp = self.get_clock().now().to_msg()
        lidar_transform.header.frame_id = "leader/base_link"
        lidar_transform.child_frame_id = "leader/base_link/navigation_lidar"
        lidar_transform.transform.translation.z = LIDAR_HEIGHT_M
        lidar_transform.transform.rotation.w = 1.0
        self.static_broadcaster.sendTransform(lidar_transform)
        self.create_subscription(Odometry, "/leader/odom", self._odom, 30)

    def _odom(self, message: Odometry) -> None:
        odom_yaw = _yaw_from_quaternion(message.pose.pose.orientation)
        transforms = []
        if self.publish_map_anchor and self.map_to_odom is None:
            yaw = self.map_yaw - odom_yaw
            cosine = math.cos(yaw)
            sine = math.sin(yaw)
            odom_x = message.pose.pose.position.x
            odom_y = message.pose.pose.position.y
            x = self.map_x - (cosine * odom_x - sine * odom_y)
            y = self.map_y - (sine * odom_x + cosine * odom_y)
            self.map_to_odom = (x, y, yaw)
            self.get_logger().info(
                "Anchored map to local odometry using the configured start pose"
            )

        if self.map_to_odom is not None:
            map_x, map_y, map_yaw = self.map_to_odom
            map_transform = TransformStamped()
            map_transform.header.stamp = message.header.stamp
            map_transform.header.frame_id = "map"
            map_transform.child_frame_id = "leader/odom"
            map_transform.transform.translation.x = map_x
            map_transform.transform.translation.y = map_y
            map_transform.transform.rotation.z = math.sin(map_yaw / 2.0)
            map_transform.transform.rotation.w = math.cos(map_yaw / 2.0)
            transforms.append(map_transform)

        base_transform = TransformStamped()
        base_transform.header.stamp = message.header.stamp
        base_transform.header.frame_id = "leader/odom"
        base_transform.child_frame_id = "leader/base_link"
        base_transform.transform.translation.x = message.pose.pose.position.x
        base_transform.transform.translation.y = message.pose.pose.position.y
        base_transform.transform.translation.z = message.pose.pose.position.z
        base_transform.transform.rotation = message.pose.pose.orientation
        transforms.append(base_transform)
        self.broadcaster.sendTransform(transforms)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = LeaderMapTf()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
