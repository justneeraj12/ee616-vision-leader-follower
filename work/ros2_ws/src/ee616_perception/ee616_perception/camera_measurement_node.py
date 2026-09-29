"""ROS node for the camera-only red-target measurement baseline."""

from __future__ import annotations

import math

from cv_bridge import CvBridge
from ee616_perception.red_target import detect_red_target
from geometry_msgs.msg import Vector3Stamped
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


class CameraMeasurementNode(Node):
    """Convert camera images into relative range and bearing measurements."""

    def __init__(self) -> None:
        super().__init__("camera_measurement")
        self.declare_parameter("image_topic", "/smoke/camera/image")
        self.declare_parameter("measurement_topic", "measurement/relative")
        self.declare_parameter("horizontal_fov_rad", 1.2217304764)
        self.declare_parameter("target_height_m", 0.9)
        self.declare_parameter("min_saturation", 80)
        self.declare_parameter("min_value", 50)
        self.declare_parameter("min_area_px", 80.0)
        self.declare_parameter("min_height_px", 5)

        image_topic = str(self.get_parameter("image_topic").value)
        measurement_topic = str(
            self.get_parameter("measurement_topic").value
        )
        self.horizontal_fov_rad = float(
            self.get_parameter("horizontal_fov_rad").value
        )
        self.target_height_m = float(
            self.get_parameter("target_height_m").value
        )
        self.min_saturation = int(
            self.get_parameter("min_saturation").value
        )
        self.min_value = int(self.get_parameter("min_value").value)
        self.min_area_px = float(self.get_parameter("min_area_px").value)
        self.min_height_px = int(
            self.get_parameter("min_height_px").value
        )

        self.bridge = CvBridge()
        self.publisher = self.create_publisher(
            Vector3Stamped,
            measurement_topic,
            10,
        )
        self.subscription = self.create_subscription(
            Image,
            image_topic,
            self._receive_image,
            qos_profile_sensor_data,
        )
        self.frames = 0

    def _receive_image(self, message: Image) -> None:
        try:
            rgb_image = self.bridge.imgmsg_to_cv2(
                message,
                desired_encoding="rgb8",
            )
            result = detect_red_target(
                rgb_image,
                horizontal_fov_rad=self.horizontal_fov_rad,
                target_height_m=self.target_height_m,
                min_saturation=self.min_saturation,
                min_value=self.min_value,
                min_area_px=self.min_area_px,
                min_height_px=self.min_height_px,
            )
        except (ValueError, TypeError) as exc:
            self.get_logger().error(f"Image conversion or detection failed: {exc}")
            return

        output = Vector3Stamped()
        output.header = message.header
        output.header.frame_id = "camera_measurement"
        output.vector.x = result.range_m if result.valid else math.nan
        output.vector.y = result.bearing_rad if result.valid else math.nan
        output.vector.z = 1.0 if result.valid else 0.0
        self.publisher.publish(output)
        self.frames += 1
        if self.frames % 150 == 0:
            self.get_logger().info(f"Processed {self.frames} camera frames")


def main(args=None) -> None:
    rclpy.init(args=args)
    node = CameraMeasurementNode()
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
