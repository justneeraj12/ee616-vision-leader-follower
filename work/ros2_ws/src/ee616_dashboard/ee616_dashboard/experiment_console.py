"""Run validated warehouse profiles and expose read-only live telemetry."""

from __future__ import annotations

import json
import math
import os
import signal
import subprocess
import threading
import time
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from ament_index_python.packages import get_package_share_directory
from ee616_dashboard.configuration import (
    ExperimentConfig,
    MAP_PROFILES,
    ROUTE_PROFILES,
    SCENARIO_PROFILES,
)
from geometry_msgs.msg import Twist, Vector3Stamped
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, Float32MultiArray, String


MAX_REQUEST_BYTES = 16_384


class MissionProcess:
    """Own at most one validated ROS launch subprocess."""

    def __init__(self, output_root: Path) -> None:
        self.output_root = output_root.resolve()
        self._lock = threading.Lock()
        self._process: subprocess.Popen | None = None
        self._log_handle = None
        self._config: ExperimentConfig | None = None
        self._output_dir: Path | None = None
        self._started_at: str | None = None
        self._last_exit_code: int | None = None

    def _refresh_locked(self) -> None:
        if self._process is None:
            return
        exit_code = self._process.poll()
        if exit_code is None:
            return
        self._last_exit_code = exit_code
        self._process = None
        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None

    def start(self, config: ExperimentConfig) -> dict:
        with self._lock:
            self._refresh_locked()
            if self._process is not None:
                raise RuntimeError("an experiment is already running")
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            name = (
                f"{timestamp}_{config.map_profile}_{config.route_profile}_"
                f"{config.scenario_profile}_"
                f"{config.follower_count}f"
            )
            output_dir = (self.output_root / name).resolve()
            if self.output_root not in output_dir.parents:
                raise RuntimeError("refused output directory outside result root")
            output_dir.mkdir(parents=True, exist_ok=False)
            log_handle = (output_dir / "launch.log").open(
                "w", encoding="utf-8"
            )
            command = config.launch_command(output_dir)
            self._process = subprocess.Popen(
                command,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                text=True,
            )
            self._log_handle = log_handle
            self._config = config
            self._output_dir = output_dir
            self._started_at = datetime.now(timezone.utc).isoformat()
            self._last_exit_code = None
            return self._status_locked()

    def stop(self) -> dict:
        with self._lock:
            self._refresh_locked()
            process = self._process
            if process is None:
                return self._status_locked()
            os.killpg(process.pid, signal.SIGINT)
        try:
            process.wait(timeout=12.0)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5.0)
        with self._lock:
            self._refresh_locked()
            return self._status_locked()

    def _status_locked(self) -> dict:
        running = self._process is not None
        return {
            "running": running,
            "pid": self._process.pid if running else None,
            "config": self._config.as_dict() if self._config else None,
            "output_dir": str(self._output_dir) if self._output_dir else None,
            "started_at": self._started_at,
            "last_exit_code": self._last_exit_code,
        }

    def status(self) -> dict:
        with self._lock:
            self._refresh_locked()
            return self._status_locked()


class TelemetryStore:
    """Thread-safe, non-control telemetry state shared with the web server."""

    def __init__(self, process: MissionProcess) -> None:
        self.process = process
        self._lock = threading.Lock()
        self.started_monotonic = time.monotonic()
        self.mission_state = "IDLE"
        self.planner_state: dict = {}
        self.governor_state: dict = {}
        self.cargo: dict = {}
        self.followers = {
            str(index): {
                "state": "OFFLINE",
                "estimated_range_m": None,
                "estimated_bearing_deg": None,
                "measurement_age_s": None,
                "estimated_spacing_error_m": None,
                "estimated_rmse_m": None,
                "linear_cmd_mps": 0.0,
                "angular_cmd_rps": 0.0,
                "inference_ms": None,
                "detection_confidence": None,
                "sample_count": 0,
                "last_update_monotonic": None,
                "sum_squared_error": 0.0,
            }
            for index in range(1, 4)
        }
        self.resources: dict = {}

    def reset_run_metrics(self) -> None:
        """Clear values that must not leak between experiment runs."""
        with self._lock:
            self.mission_state = "STARTING"
            self.planner_state = {}
            self.governor_state = {}
            self.cargo = {}
            for follower in self.followers.values():
                follower.update({
                    "state": "OFFLINE",
                    "estimated_range_m": None,
                    "estimated_bearing_deg": None,
                    "measurement_age_s": None,
                    "estimated_spacing_error_m": None,
                    "estimated_rmse_m": None,
                    "linear_cmd_mps": 0.0,
                    "angular_cmd_rps": 0.0,
                    "inference_ms": None,
                    "detection_confidence": None,
                    "sample_count": 0,
                    "last_update_monotonic": None,
                    "sum_squared_error": 0.0,
                })

    def update_json(self, field: str, text: str) -> None:
        try:
            value = json.loads(text)
        except (TypeError, json.JSONDecodeError):
            return
        if not isinstance(value, dict):
            return
        with self._lock:
            setattr(self, field, value)

    def update_follower(self, index: int, **values) -> None:
        with self._lock:
            follower = self.followers[str(index)]
            follower.update(values)
            follower["last_update_monotonic"] = time.monotonic()

    def update_estimate(
        self,
        index: int,
        range_m: float,
        bearing_rad: float,
        age_s: float,
    ) -> None:
        error_m = range_m - 1.5
        with self._lock:
            follower = self.followers[str(index)]
            follower["estimated_range_m"] = finite_or_none(range_m)
            follower["estimated_bearing_deg"] = finite_or_none(
                math.degrees(bearing_rad)
            )
            follower["measurement_age_s"] = finite_or_none(age_s)
            follower["estimated_spacing_error_m"] = finite_or_none(error_m)
            if math.isfinite(error_m):
                follower["sample_count"] += 1
                follower["sum_squared_error"] += error_m * error_m
                follower["estimated_rmse_m"] = math.sqrt(
                    follower["sum_squared_error"] / follower["sample_count"]
                )
            follower["last_update_monotonic"] = time.monotonic()

    def snapshot(self) -> dict:
        process_status = self.process.status()
        active_count = (
            process_status["config"]["follower_count"]
            if process_status["config"] else 3
        )
        now = time.monotonic()
        with self._lock:
            followers = {}
            for key, values in self.followers.items():
                public = {
                    name: value
                    for name, value in values.items()
                    if name not in {"sum_squared_error", "last_update_monotonic"}
                }
                stamp = values["last_update_monotonic"]
                public["telemetry_age_s"] = (
                    round(now - stamp, 3) if stamp is not None else None
                )
                public["active"] = int(key) <= active_count
                followers[key] = public
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_s": round(now - self.started_monotonic, 2),
                "mission_state": self.mission_state,
                "planner": dict(self.planner_state),
                "governor": dict(self.governor_state),
                "cargo": dict(self.cargo),
                "followers": followers,
                "resources": dict(self.resources),
                "process": process_status,
                "metric_boundary": (
                    "Live spacing error and RMSE use the EKF estimate. Gazebo "
                    "ground truth remains evaluation-only and is written to the "
                    "post-run result files."
                ),
            }


def finite_or_none(value: float) -> float | None:
    return float(value) if math.isfinite(value) else None


class ExperimentConsoleNode(Node):
    """Collect ROS telemetry while never publishing into robot control."""

    def __init__(self, process: MissionProcess) -> None:
        super().__init__("experiment_console")
        self.store = TelemetryStore(process)
        self.create_subscription(
            String, "/warehouse_mission/state", self._mission, 10
        )
        self.create_subscription(
            String, "/warehouse_nav/planner_state", self._planner, 10
        )
        self.create_subscription(
            String, "/warehouse_nav/governor_state", self._governor, 10
        )
        self.create_subscription(
            String, "/warehouse_mission/cargo_state", self._cargo, 10
        )
        for index in range(1, 4):
            prefix = f"/follower_{index}"
            self.create_subscription(
                String,
                f"{prefix}/control/state",
                lambda message, i=index: self.store.update_follower(
                    i, state=message.data
                ),
                10,
            )
            self.create_subscription(
                Vector3Stamped,
                f"{prefix}/control/estimate",
                lambda message, i=index: self.store.update_estimate(
                    i,
                    message.vector.x,
                    message.vector.y,
                    message.vector.z,
                ),
                10,
            )
            self.create_subscription(
                Twist,
                f"{prefix}/cmd_vel",
                lambda message, i=index: self.store.update_follower(
                    i,
                    linear_cmd_mps=message.linear.x,
                    angular_cmd_rps=message.angular.z,
                ),
                10,
            )
            self.create_subscription(
                Float32,
                f"{prefix}/measurement/inference_ms",
                lambda message, i=index: self.store.update_follower(
                    i, inference_ms=finite_or_none(message.data)
                ),
                10,
            )
            self.create_subscription(
                Float32MultiArray,
                f"{prefix}/measurement/detection_box",
                lambda message, i=index: self._detection(i, message),
                10,
            )
        self.create_timer(2.0, self._sample_resources)

    def _mission(self, message: String) -> None:
        with self.store._lock:
            self.store.mission_state = message.data

    def _planner(self, message: String) -> None:
        self.store.update_json("planner_state", message.data)

    def _governor(self, message: String) -> None:
        self.store.update_json("governor_state", message.data)

    def _cargo(self, message: String) -> None:
        self.store.update_json("cargo", message.data)

    def _detection(self, index: int, message: Float32MultiArray) -> None:
        confidence = message.data[0] if message.data else math.nan
        self.store.update_follower(
            index, detection_confidence=finite_or_none(confidence)
        )

    def _sample_resources(self) -> None:
        resources = {"load_average_1m": round(os.getloadavg()[0], 2)}
        memory_current = Path("/sys/fs/cgroup/memory.current")
        if memory_current.exists():
            try:
                resources["container_memory_mib"] = round(
                    int(memory_current.read_text().strip()) / 1024**2, 1
                )
            except (OSError, ValueError):
                pass
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu,memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                check=True,
                text=True,
                timeout=1.0,
            )
            values = [value.strip() for value in result.stdout.splitlines()[0].split(",")]
            resources.update({
                "gpu_utilization_percent": float(values[0]),
                "gpu_memory_used_mib": float(values[1]),
                "gpu_memory_total_mib": float(values[2]),
            })
        except (FileNotFoundError, IndexError, subprocess.SubprocessError, ValueError):
            resources["gpu_status"] = "unavailable"
        resources["components"] = self._component_resources()
        with self.store._lock:
            self.store.resources = resources

    @staticmethod
    def _component_resources() -> dict:
        """Attribute process CPU and resident memory by functional stack."""
        groups = {
            "leader_navigation": {
                "tokens": (
                    "planner_server", "controller_server", "amcl",
                    "map_server", "leader_map_tf", "warehouse_nav_mission",
                    "convoy_governor",
                ),
                "cpu_percent": 0.0,
                "memory_mib": 0.0,
                "process_count": 0,
            },
            "follower_perception_control": {
                "tokens": ("yolo_measurement", "follower_controller"),
                "cpu_percent": 0.0,
                "memory_mib": 0.0,
                "process_count": 0,
            },
            "simulation_evaluation": {
                "tokens": ("gz sim", "parameter_bridge", "mission_evaluator"),
                "cpu_percent": 0.0,
                "memory_mib": 0.0,
                "process_count": 0,
            },
        }
        try:
            result = subprocess.run(
                ["ps", "-eo", "rss=,pcpu=,args="],
                capture_output=True,
                check=True,
                text=True,
                timeout=1.0,
            )
            for line in result.stdout.splitlines():
                parts = line.strip().split(None, 2)
                if len(parts) != 3:
                    continue
                rss_kib, cpu_percent, command = parts
                for values in groups.values():
                    if any(token in command for token in values["tokens"]):
                        values["cpu_percent"] += float(cpu_percent)
                        values["memory_mib"] += float(rss_kib) / 1024.0
                        values["process_count"] += 1
                        break
        except (FileNotFoundError, subprocess.SubprocessError, ValueError):
            return {}
        return {
            name: {
                "cpu_percent": round(values["cpu_percent"], 1),
                "memory_mib": round(values["memory_mib"], 1),
                "process_count": values["process_count"],
            }
            for name, values in groups.items()
        }


def make_handler(store: TelemetryStore, process: MissionProcess, web_root: Path):
    """Create an HTTP handler bound to this console instance."""

    class ConsoleHandler(BaseHTTPRequestHandler):
        assets = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            "/styles.css": ("styles.css", "text/css; charset=utf-8"),
        }

        def log_message(self, format_string: str, *args) -> None:
            return

        def _json(self, status: HTTPStatus, payload: dict) -> None:
            encoded = json.dumps(payload, allow_nan=False).encode("utf-8")
            self.send_response(status.value)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/api/telemetry":
                self._json(HTTPStatus.OK, store.snapshot())
                return
            if path == "/api/profiles":
                self._json(HTTPStatus.OK, {
                    "routes": ROUTE_PROFILES,
                    "maps": MAP_PROFILES,
                    "scenarios": SCENARIO_PROFILES,
                    "follower_counts": [1, 2, 3],
                    "scenario": "nominal_mapped_mission",
                })
                return
            if path not in self.assets:
                self.send_error(HTTPStatus.NOT_FOUND.value)
                return
            filename, content_type = self.assets[path]
            content = (web_root / filename).read_bytes()
            self.send_response(HTTPStatus.OK.value)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid length"})
                return
            if length > MAX_REQUEST_BYTES:
                self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {
                    "error": "request is too large"
                })
                return
            try:
                body = self.rfile.read(length)
                values = json.loads(body or b"{}")
                if not isinstance(values, dict):
                    raise ValueError("request body must be a JSON object")
                if path == "/api/start":
                    config = ExperimentConfig.from_mapping(values)
                    store.reset_run_metrics()
                    payload = process.start(config)
                elif path == "/api/stop":
                    payload = process.stop()
                else:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                    return
            except (json.JSONDecodeError, ValueError, RuntimeError) as error:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
                return
            self._json(HTTPStatus.OK, payload)

    return ConsoleHandler


def main(args=None) -> None:
    rclpy.init(args=args)
    project_root = Path(os.environ.get("EE616_PROJECT_ROOT", "/workspace"))
    output_root = project_root / "work" / "ros2_ws" / "results" / "dashboard_runs"
    process = MissionProcess(output_root)
    node = ExperimentConsoleNode(process)
    web_root = (
        Path(get_package_share_directory("ee616_dashboard")) / "web"
    )
    server = ThreadingHTTPServer(
        ("127.0.0.1", 8765),
        make_handler(node.store, process, web_root),
    )
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    node.get_logger().info("Experiment console: http://127.0.0.1:8765")
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        process.stop()
        server.shutdown()
        server.server_close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
