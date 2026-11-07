"""Bound leader motion from follower health without consuming ground truth."""

from __future__ import annotations

import json
import math

from ee616_control.convoy_governor import (
    FollowerHealth,
    decide_governor,
    navigation_active,
)
from geometry_msgs.msg import Twist, Vector3Stamped
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ConvoyGovernorNode(Node):
    """Proxy leader commands and publish an auditable convoy-health state."""

    def __init__(self) -> None:
        super().__init__("convoy_governor")
        self.declare_parameter("follower_count", 3)
        self.declare_parameter("caution_scale", 0.55)
        self.declare_parameter("bearing_caution_rad", 0.35)
        self.declare_parameter("measurement_age_caution_s", 0.20)
        self.declare_parameter("turn_caution_angular_rps", 0.12)
        self.declare_parameter("telemetry_timeout_s", 0.75)
        self.declare_parameter("recovery_stable_s", 1.0)
        self.declare_parameter("fault_mode", "none")
        self.declare_parameter("fault_start_s", 18.0)
        self.declare_parameter("fault_duration_s", 3.0)
        self.follower_count = int(self.get_parameter("follower_count").value)
        if self.follower_count not in {1, 2, 3}:
            raise ValueError("follower_count must be 1, 2, or 3")
        self.caution_scale = float(self.get_parameter("caution_scale").value)
        self.bearing_caution_rad = float(
            self.get_parameter("bearing_caution_rad").value
        )
        self.measurement_age_caution_s = float(
            self.get_parameter("measurement_age_caution_s").value
        )
        self.turn_caution_angular_rps = float(
            self.get_parameter("turn_caution_angular_rps").value
        )
        self.telemetry_timeout_s = float(
            self.get_parameter("telemetry_timeout_s").value
        )
        self.recovery_stable_s = float(
            self.get_parameter("recovery_stable_s").value
        )
        self.fault_mode = str(self.get_parameter("fault_mode").value)
        if self.fault_mode not in {"none", "leader_cmd_dropout"}:
            raise ValueError("fault_mode must be none or leader_cmd_dropout")
        self.fault_start_s = float(self.get_parameter("fault_start_s").value)
        self.fault_duration_s = float(
            self.get_parameter("fault_duration_s").value
        )
        self.mission_state = "UNSEEN"
        self.mission_command = Twist()
        self.nav_command = Twist()
        self.nav_command_stamp_s: float | None = None
        self.navigation_started_s: float | None = None
        self.followers = {
            index: {
                "state": "UNSEEN",
                "bearing_rad": None,
                "measurement_age_s": None,
                "telemetry_stamp_s": None,
            }
            for index in range(1, self.follower_count + 1)
        }
        self.previous_mode = "STARTING"
        self.healthy_since_s: float | None = None
        self.publisher = self.create_publisher(Twist, "/leader/cmd_vel", 10)
        self.state_publisher = self.create_publisher(
            String, "/warehouse_nav/governor_state", 10
        )
        self.create_subscription(
            Twist, "/leader/mission_cmd_vel", self._mission_command, 10
        )
        self.create_subscription(
            Twist, "/leader/nav_cmd_vel", self._nav_command, 10
        )
        self.create_subscription(
            String, "/warehouse_mission/state", self._mission_state, 10
        )
        for index in range(1, self.follower_count + 1):
            prefix = f"/follower_{index}"
            self.create_subscription(
                String,
                f"{prefix}/control/state",
                lambda message, i=index: self._follower_state(i, message),
                10,
            )
            self.create_subscription(
                Vector3Stamped,
                f"{prefix}/control/estimate",
                lambda message, i=index: self._follower_estimate(i, message),
                10,
            )
        self.timer = self.create_timer(0.05, self._tick)

    def _now_s(self) -> float:
        return self.get_clock().now().nanoseconds * 1.0e-9

    def _mission_command(self, message: Twist) -> None:
        self.mission_command = message

    def _nav_command(self, message: Twist) -> None:
        self.nav_command = message
        self.nav_command_stamp_s = self._now_s()

    def _mission_state(self, message: String) -> None:
        self.mission_state = message.data
        if navigation_active(message.data) and self.navigation_started_s is None:
            self.navigation_started_s = self._now_s()

    def _follower_state(self, index: int, message: String) -> None:
        self.followers[index]["state"] = message.data
        self.followers[index]["telemetry_stamp_s"] = self._now_s()

    def _follower_estimate(self, index: int, message: Vector3Stamped) -> None:
        bearing = float(message.vector.y)
        age = float(message.vector.z)
        self.followers[index]["bearing_rad"] = (
            bearing if math.isfinite(bearing) else None
        )
        self.followers[index]["measurement_age_s"] = (
            age if math.isfinite(age) else None
        )
        self.followers[index]["telemetry_stamp_s"] = self._now_s()

    def _fault_active(self, now_s: float) -> bool:
        if self.fault_mode != "leader_cmd_dropout":
            return False
        if self.navigation_started_s is None:
            return False
        elapsed = now_s - self.navigation_started_s
        return self.fault_start_s <= elapsed < (
            self.fault_start_s + self.fault_duration_s
        )

    def _health(self, now_s: float) -> list[FollowerHealth]:
        health = []
        for values in self.followers.values():
            stamp = values["telemetry_stamp_s"]
            health.append(FollowerHealth(
                state=str(values["state"]),
                bearing_rad=values["bearing_rad"],
                measurement_age_s=values["measurement_age_s"],
                telemetry_age_s=now_s - stamp if stamp is not None else None,
            ))
        return health

    @staticmethod
    def _scaled(command: Twist, linear_scale: float) -> Twist:
        output = Twist()
        output.linear.x = max(0.0, min(0.6, command.linear.x * linear_scale))
        output.angular.z = max(
            -0.8, min(0.8, command.angular.z * linear_scale)
        )
        return output

    def _tick(self) -> None:
        now_s = self._now_s()
        health = self._health(now_s)
        decision = decide_governor(
            health,
            mission_state=self.mission_state,
            fault_active=self._fault_active(now_s),
            bearing_caution_rad=self.bearing_caution_rad,
            measurement_age_caution_s=self.measurement_age_caution_s,
            telemetry_timeout_s=self.telemetry_timeout_s,
            caution_scale=self.caution_scale,
        )
        if (
            decision.mode == "NORMAL"
            and navigation_active(self.mission_state)
            and abs(self.nav_command.angular.z) >= self.turn_caution_angular_rps
        ):
            decision = type(decision)(
                "CAUTION",
                "leader path command indicates a turn",
                self.caution_scale,
                False,
            )
        if decision.mode == "NORMAL":
            if self.previous_mode in {"HOLD", "FAULT_HOLD", "RECOVERY_HOLD"}:
                if self.healthy_since_s is None:
                    self.healthy_since_s = now_s
                if now_s - self.healthy_since_s < self.recovery_stable_s:
                    decision = type(decision)(
                        "RECOVERY_HOLD",
                        "waiting for stable TRACK before resuming",
                        0.0,
                        True,
                    )
            else:
                self.healthy_since_s = now_s
        else:
            self.healthy_since_s = None

        source = "mission"
        base = self.mission_command
        if navigation_active(self.mission_state):
            source = "nav2"
            base = self.nav_command
            if (
                self.nav_command_stamp_s is None
                or now_s - self.nav_command_stamp_s > 0.50
            ):
                decision = type(decision)(
                    "HOLD", "leader Nav2 command is stale", 0.0, True
                )
        output = Twist() if decision.hold else self._scaled(
            base, decision.linear_scale
        )
        self.publisher.publish(output)
        status = String()
        status.data = json.dumps({
            "mode": decision.mode,
            "reason": decision.reason,
            "linear_scale": decision.linear_scale,
            "mission_state": self.mission_state,
            "command_source": source,
            "fault_mode": self.fault_mode,
            "fault_active": self._fault_active(now_s),
            "output_linear_mps": output.linear.x,
            "output_angular_rps": output.angular.z,
            "followers": {
                str(index): {
                    "state": item.state,
                    "bearing_rad": item.bearing_rad,
                    "measurement_age_s": item.measurement_age_s,
                    "telemetry_age_s": item.telemetry_age_s,
                }
                for index, item in enumerate(health, start=1)
            },
            "ground_truth_used": False,
        }, sort_keys=True)
        self.state_publisher.publish(status)
        self.previous_mode = decision.mode

    def destroy_node(self):
        if rclpy.ok():
            self.publisher.publish(Twist())
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ConvoyGovernorNode()
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
