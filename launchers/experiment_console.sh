#!/usr/bin/env bash
set -euo pipefail

launcher_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd -- "${launcher_dir}/.." && pwd)"

(
    for _attempt in $(seq 1 90); do
        if curl --fail --silent http://127.0.0.1:8765/api/profiles >/dev/null; then
            xdg-open http://127.0.0.1:8765 >/dev/null 2>&1 || true
            exit 0
        fi
        sleep 1
    done
) &
cd "${project_root}"
echo "Starting the configurable EE 616 experiment console"
echo "If the browser does not open, visit http://127.0.0.1:8765"
exec make experiment-console
