import sys
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class NamespaceProbe(Node):
    """Verify that a relative topic remains inside the node namespace."""

    def __init__(self) -> None:
        super().__init__("namespace_probe")
        self.declare_parameter("expected_id", "unset")
        self.declare_parameter("required_samples", 5)
        self.declare_parameter("timeout_s", 5.0)

        self.expected_id = str(self.get_parameter("expected_id").value)
        self.required_samples = int(self.get_parameter("required_samples").value)
        self.deadline = time.monotonic() + float(self.get_parameter("timeout_s").value)
        self.received = 0
        self.failure = ""

        self.publisher = self.create_publisher(String, "heartbeat", 10)
        self.subscription = self.create_subscription(String, "heartbeat", self._receive, 10)
        self.timer = self.create_timer(0.1, self._tick)

    def _receive(self, message: String) -> None:
        if message.data != self.expected_id:
            self.failure = f"received {message.data!r}; expected {self.expected_id!r}"
            rclpy.shutdown()
            return

        self.received += 1
        if self.received >= self.required_samples:
            self.get_logger().info(
                f"PASS namespace={self.get_namespace()} samples={self.received}"
            )
            rclpy.shutdown()

    def _tick(self) -> None:
        message = String()
        message.data = self.expected_id
        self.publisher.publish(message)

        if time.monotonic() >= self.deadline and rclpy.ok():
            self.failure = f"timed out after receiving {self.received} samples"
            rclpy.shutdown()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = NamespaceProbe()
    try:
        rclpy.spin(node)
    finally:
        failure = node.failure
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

    if failure:
        print(f"FAIL: {failure}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
