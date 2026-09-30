"""ROS node for isolated YOLO camera measurements."""

from __future__ import annotations

import math

from cv_bridge import CvBridge
from ee616_perception.yolo_target import YoloTargetDetector
from geometry_msgs.msg import Vector3Stamped
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import Float32, Float32MultiArray


class YoloMeasurementNode(Node):
    """Publish range and bearing from RGB images using one trained model."""

    def __init__(self) -> None:
        super().__init__("yolo_measurement")
        self.declare_parameter("image_topic", "/smoke/camera/image")
        self.declare_parameter("measurement_topic", "measurement/relative")
        self.declare_parameter("latency_topic", "measurement/inference_ms")
        self.declare_parameter("diagnostic_topic", "measurement/detection_box")
        self.declare_parameter("horizontal_fov_rad", 1.2217304764)
        self.declare_parameter("target_height_m", 0.9)
        self.declare_parameter(
            "weights_path",
            "/workspace/work/ros2_ws/models/yolov8n_predecessor_v1.pt",
        )
        self.declare_parameter("class_id", 0)
        self.declare_parameter("confidence", 0.25)
        self.declare_parameter("iou", 0.45)
        self.declare_parameter("image_size", 640)
        self.declare_parameter("device", "0")
        self.declare_parameter("range_scale", 1.0)
        self.declare_parameter("range_offset_m", 0.0)

        self.horizontal_fov_rad = float(
            self.get_parameter("horizontal_fov_rad").value
        )
        self.target_height_m = float(
            self.get_parameter("target_height_m").value
        )
        self.detector = YoloTargetDetector(
            str(self.get_parameter("weights_path").value),
            class_id=int(self.get_parameter("class_id").value),
            confidence=float(self.get_parameter("confidence").value),
            iou=float(self.get_parameter("iou").value),
            image_size=int(self.get_parameter("image_size").value),
            device=str(self.get_parameter("device").value),
            range_scale=float(self.get_parameter("range_scale").value),
            range_offset_m=float(self.get_parameter("range_offset_m").value),
        )
        self.bridge = CvBridge()
        self.measurement_publisher = self.create_publisher(
            Vector3Stamped,
            str(self.get_parameter("measurement_topic").value),
            10,
        )
        self.latency_publisher = self.create_publisher(
            Float32,
            str(self.get_parameter("latency_topic").value),
            10,
        )
        self.diagnostic_publisher = self.create_publisher(
            Float32MultiArray,
            str(self.get_parameter("diagnostic_topic").value),
            10,
        )
        self.subscription = self.create_subscription(
            Image,
            str(self.get_parameter("image_topic").value),
            self._receive_image,
            qos_profile_sensor_data,
        )

    def _receive_image(self, message: Image) -> None:
        try:
            rgb_image = self.bridge.imgmsg_to_cv2(
                message,
                desired_encoding="rgb8",
            )
            result = self.detector.detect(
                rgb_image,
                horizontal_fov_rad=self.horizontal_fov_rad,
                target_height_m=self.target_height_m,
            )
        except (RuntimeError, TypeError, ValueError) as exc:
            self.get_logger().error(f"YOLO image processing failed: {exc}")
            return

        output = Vector3Stamped()
        output.header = message.header
        output.header.frame_id = "camera_measurement"
        output.vector.x = result.range_m if result.valid else math.nan
        output.vector.y = result.bearing_rad if result.valid else math.nan
        output.vector.z = 1.0 if result.valid else 0.0
        latency = Float32()
        latency.data = float(self.detector.last_inference_ms)
        self.latency_publisher.publish(latency)
        diagnostic = Float32MultiArray()
        if result.valid:
            diagnostic.data = [
                float(self.detector.last_confidence),
                float(result.bbox_x),
                float(result.bbox_y),
                float(result.bbox_width),
                float(result.bbox_height),
            ]
        else:
            diagnostic.data = [math.nan, math.nan, math.nan, math.nan, math.nan]
        self.diagnostic_publisher.publish(diagnostic)
        self.measurement_publisher.publish(output)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = YoloMeasurementNode()
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
