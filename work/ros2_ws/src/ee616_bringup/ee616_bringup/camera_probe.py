import json
import sys
import time
from pathlib import Path

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class CameraProbe(Node):
    """Collect a bounded camera sample and write a machine-readable result."""

    def __init__(self) -> None:
        super().__init__("camera_probe")
        self.declare_parameter("topic", "/smoke/camera/image")
        self.declare_parameter("required_samples", 15)
        self.declare_parameter("timeout_s", 20.0)
        self.declare_parameter(
            "output_path",
            "/workspace/work/ros2_ws/results/environment_gate/camera_probe.json",
        )

        self.topic = str(self.get_parameter("topic").value)
        self.required_samples = int(self.get_parameter("required_samples").value)
        self.timeout_s = float(self.get_parameter("timeout_s").value)
        self.output_path = Path(str(self.get_parameter("output_path").value))
        self.started = time.monotonic()
        self.received_times = []
        self.width = 0
        self.height = 0
        self.encoding = ""
        self.nonzero_stamps = 0
        self.failure = ""

        self.subscription = self.create_subscription(Image, self.topic, self._receive, 10)
        self.timer = self.create_timer(0.25, self._check_timeout)

    def _receive(self, message: Image) -> None:
        self.received_times.append(time.monotonic())
        self.width = int(message.width)
        self.height = int(message.height)
        self.encoding = message.encoding
        if message.header.stamp.sec != 0 or message.header.stamp.nanosec != 0:
            self.nonzero_stamps += 1

        if self.width <= 0 or self.height <= 0:
            self.failure = "received an image with invalid dimensions"
            rclpy.shutdown()
        elif len(self.received_times) >= self.required_samples:
            rclpy.shutdown()

    def _check_timeout(self) -> None:
        if time.monotonic() - self.started >= self.timeout_s:
            self.failure = f"timed out after {len(self.received_times)} images"
            rclpy.shutdown()

    def write_result(self) -> bool:
        elapsed = 0.0
        if len(self.received_times) > 1:
            elapsed = self.received_times[-1] - self.received_times[0]
        measured_hz = (
            (len(self.received_times) - 1) / elapsed if elapsed > 0.0 else 0.0
        )
        passed = not self.failure and len(self.received_times) >= self.required_samples
        result = {
            "status": "pass" if passed else "fail",
            "topic": self.topic,
            "samples": len(self.received_times),
            "required_samples": self.required_samples,
            "width": self.width,
            "height": self.height,
            "encoding": self.encoding,
            "measured_receive_hz": measured_hz,
            "nonzero_timestamp_samples": self.nonzero_stamps,
            "failure": self.failure or None,
            "scope": "camera transport smoke test; not measurement-accuracy evidence",
        }
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return passed


def main(args=None) -> None:
    rclpy.init(args=args)
    node = CameraProbe()
    try:
        rclpy.spin(node)
    finally:
        passed = node.write_result()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

    if not passed:
        print("Camera probe failed; see the JSON result.", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
