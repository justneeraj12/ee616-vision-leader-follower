"""Read-only follower-camera and supervisor dashboard for live demonstrations."""

from __future__ import annotations

import time

from cv_bridge import CvBridge
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import String


PANEL_WIDTH = 560
PANEL_HEIGHT = 420
HEADER_HEIGHT = 70


def compose_dashboard(
    images: dict[int, np.ndarray],
    states: dict[int, str],
    ages_s: dict[int, float],
    follower_count: int,
    event: str,
    camera_count: int | None = None,
) -> np.ndarray:
    """Return one annotated panel per follower without publishing any data."""
    if camera_count is None:
        camera_count = follower_count
    panels = []
    for index in range(1, follower_count + 1):
        image = images.get(index)
        if image is None:
            body = np.full(
                (PANEL_HEIGHT - HEADER_HEIGHT, PANEL_WIDTH, 3), 28, dtype=np.uint8
            )
            waiting_text = (
                "WAITING FOR CAMERA"
                if index <= camera_count
                else "STATE ONLY - CAMERA NOT SHOWN"
            )
            cv2.putText(
                body, waiting_text, (45, 180), cv2.FONT_HERSHEY_SIMPLEX,
                0.9, (180, 180, 180), 2, cv2.LINE_AA,
            )
        else:
            body = cv2.resize(
                image, (PANEL_WIDTH, PANEL_HEIGHT - HEADER_HEIGHT),
                interpolation=cv2.INTER_AREA,
            )
        panel = np.zeros((PANEL_HEIGHT, PANEL_WIDTH, 3), dtype=np.uint8)
        state = states.get(index, "WAITING")
        state_color = {
            "TRACK": (70, 200, 90),
            "PREDICT": (0, 190, 255),
            "SAFE_STOP": (40, 40, 230),
        }.get(state, (170, 170, 170))
        age = ages_s.get(index)
        age_text = "no frame" if age is None else f"frame age {age:.2f} s"
        cv2.putText(
            panel, f"Follower {index}", (18, 30), cv2.FONT_HERSHEY_SIMPLEX,
            0.75, (245, 245, 245), 2, cv2.LINE_AA,
        )
        cv2.putText(
            panel, state, (210, 30), cv2.FONT_HERSHEY_SIMPLEX,
            0.75, state_color, 2, cv2.LINE_AA,
        )
        cv2.putText(
            panel, age_text, (18, 58), cv2.FONT_HERSHEY_SIMPLEX,
            0.55, (190, 200, 210), 1, cv2.LINE_AA,
        )
        cv2.putText(
            panel, f"event: {event}", (290, 58), cv2.FONT_HERSHEY_SIMPLEX,
            0.55, (120, 210, 255) if event != "NONE" else (160, 160, 160),
            1, cv2.LINE_AA,
        )
        panel[HEADER_HEIGHT:] = body
        panels.append(panel)
    return np.hstack(panels)


class DemoViewerNode(Node):
    """Display RGB and controller state while remaining outside the control path."""

    def __init__(self) -> None:
        super().__init__("demo_viewer")
        self.declare_parameter("follower_count", 1)
        self.declare_parameter("camera_count", 1)
        self.declare_parameter("disturbed_images", False)
        self.declare_parameter("event_topic", "/experiment/event")
        self.follower_count = int(self.get_parameter("follower_count").value)
        self.camera_count = int(self.get_parameter("camera_count").value)
        if self.follower_count not in {1, 2, 3}:
            raise ValueError("follower_count must be 1, 2, or 3")
        if not 1 <= self.camera_count <= self.follower_count:
            raise ValueError("camera_count must be between 1 and follower_count")
        disturbed = bool(self.get_parameter("disturbed_images").value)
        image_leaf = "camera/disturbed" if disturbed else "camera/image"
        self.bridge = CvBridge()
        self.images: dict[int, np.ndarray] = {}
        self.pending_images: dict[int, Image] = {}
        self.frame_times: dict[int, float] = {}
        self.states: dict[int, str] = {}
        self.event = "NONE"
        self.window_name = "EE616 follower cameras and supervisor states"
        for index in range(1, self.follower_count + 1):
            if index <= self.camera_count:
                self.create_subscription(
                    Image,
                    f"/follower_{index}/{image_leaf}",
                    lambda message, i=index: self._image(i, message),
                    qos_profile_sensor_data,
                )
            self.create_subscription(
                String,
                f"/follower_{index}/control/state",
                lambda message, i=index: self._state(i, message),
                10,
            )
        self.create_subscription(
            String, str(self.get_parameter("event_topic").value), self._event, 10
        )
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(
            self.window_name, min(1680, PANEL_WIDTH * self.follower_count), PANEL_HEIGHT
        )
        self.timer = self.create_timer(0.1, self._render)

    def _image(self, index: int, message: Image) -> None:
        # Keep only the newest message. Conversion is limited to the dashboard's
        # 10 Hz render timer instead of competing with control for every frame.
        self.pending_images[index] = message
        self.frame_times[index] = time.monotonic()

    def _state(self, index: int, message: String) -> None:
        self.states[index] = message.data

    def _event(self, message: String) -> None:
        self.event = message.data

    def _render(self) -> None:
        for index, message in list(self.pending_images.items()):
            try:
                self.images[index] = self.bridge.imgmsg_to_cv2(
                    message, desired_encoding="bgr8"
                )
            except Exception as error:  # Display failure must not affect control.
                self.get_logger().warning(f"camera {index} conversion failed: {error}")
            finally:
                self.pending_images.pop(index, None)
        now = time.monotonic()
        ages = {index: now - stamp for index, stamp in self.frame_times.items()}
        dashboard = compose_dashboard(
            self.images, self.states, ages, self.follower_count, self.event,
            self.camera_count,
        )
        cv2.imshow(self.window_name, dashboard)
        cv2.waitKey(1)

    def destroy_node(self):
        cv2.destroyAllWindows()
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = DemoViewerNode()
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
