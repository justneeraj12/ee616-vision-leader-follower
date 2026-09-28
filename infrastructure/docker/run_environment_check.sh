#!/usr/bin/env bash
set -eo pipefail

workspace=/workspace/work/ros2_ws
result_dir="${workspace}/results/environment_gate"
mkdir -p "${result_dir}"

cd "${workspace}"
source /opt/ros/jazzy/setup.bash

colcon build --symlink-install --event-handlers console_direct+
source install/setup.bash
set -u
colcon test --event-handlers console_direct+
colcon test-result --verbose \
    2>&1 | tee "${result_dir}/colcon_test_result.txt"

ros2 launch ee616_bringup namespace_smoke.launch.py \
    2>&1 | tee "${result_dir}/namespace_smoke.log"

ros2 doctor --report > "${result_dir}/ros2_doctor.txt" 2>&1 || true
gz sim --version > "${result_dir}/gazebo_version.txt" 2>&1

ros2 launch ee616_simulation camera_smoke.launch.py \
    > "${result_dir}/camera_simulation.log" 2>&1 &
simulation_pid=$!

cleanup() {
    kill "${simulation_pid}" 2>/dev/null || true
    wait "${simulation_pid}" 2>/dev/null || true
}
trap cleanup EXIT

sleep 8
timeout 25s ros2 run ee616_bringup camera_probe --ros-args \
    -p topic:=/smoke/camera/image \
    -p required_samples:=15 \
    -p output_path:="${result_dir}/camera_probe.json"

python3 /workspace/infrastructure/docker/resource_probe.py \
    --output "${result_dir}/resource_snapshot.json"

python3 - <<'PY'
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path

result_dir = Path("/workspace/work/ros2_ws/results/environment_gate")
camera = json.loads((result_dir / "camera_probe.json").read_text(encoding="utf-8"))
resources = json.loads(
    (result_dir / "resource_snapshot.json").read_text(encoding="utf-8")
)
summary = {
    "status": "pass" if camera.get("status") == "pass" else "fail",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "platform": platform.platform(),
    "ros_distro": os.environ.get("ROS_DISTRO"),
    "ros_domain_id": os.environ.get("ROS_DOMAIN_ID"),
    "gz_partition": os.environ.get("GZ_PARTITION"),
    "camera": camera,
    "resources": resources,
    "scope": "environment smoke test only; not follower-performance evidence",
}
(result_dir / "summary.json").write_text(
    json.dumps(summary, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

echo "Environment gate smoke test passed."
