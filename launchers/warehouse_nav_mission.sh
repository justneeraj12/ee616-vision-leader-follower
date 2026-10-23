#!/usr/bin/env bash
set -euo pipefail

launcher_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd -- "${launcher_dir}/.." && pwd)"

cd "${project_root}"
echo "Starting the mapped warehouse mission with Hybrid-A* and three followers"
exec make gazebo-demo DEMO_MODE=warehouse_nav_mission
