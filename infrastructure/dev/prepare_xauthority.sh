#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
target="${project_root}/.devcontainer/.Xauthority"

if [[ -z "${DISPLAY:-}" ]]; then
    echo "DISPLAY is unset. Start VS Code from the Ubuntu desktop session." >&2
    exit 1
fi

if [[ -n "${XAUTHORITY:-}" && -r "${XAUTHORITY}" ]]; then
    install -m 600 "${XAUTHORITY}" "${target}"
    echo "Prepared X11 authorization for DISPLAY=${DISPLAY}."
    exit 0
fi

# Hyprland commonly exposes a per-user XWayland socket without exporting an
# XAUTHORITY path. Verify that this logged-in user can reach the display before
# creating the empty file expected by the Compose bind mount. This does not
# relax display access with xhost and does not grant another user permission.
if command -v xdpyinfo >/dev/null 2>&1 && xdpyinfo -display "${DISPLAY}" >/dev/null 2>&1; then
    install -m 600 /dev/null "${target}"
    echo "Prepared Hyprland/XWayland display access for DISPLAY=${DISPLAY} (no cookie required)."
    exit 0
fi

echo "The desktop display is not reachable. Start the command from the logged-in desktop session." >&2
exit 1
