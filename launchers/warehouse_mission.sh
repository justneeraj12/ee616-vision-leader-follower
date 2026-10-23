#!/usr/bin/env bash
set -euo pipefail

launcher_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd -- "${launcher_dir}/.." && pwd)"

cd "${project_root}"
echo "Starting EE 616 warehouse pickup, convoy, and drop-off mission"
exec make gazebo-demo DEMO_MODE=warehouse_mission
