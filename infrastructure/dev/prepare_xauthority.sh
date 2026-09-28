#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
target="${project_root}/.devcontainer/.Xauthority"

if [[ -z "${DISPLAY:-}" ]]; then
    echo "DISPLAY is unset. Start VS Code from the Ubuntu desktop session." >&2
    exit 1
fi

if [[ -z "${XAUTHORITY:-}" || ! -r "${XAUTHORITY}" ]]; then
    echo "XAUTHORITY is unavailable. Start VS Code from the logged-in desktop session." >&2
    exit 1
fi

install -m 600 "${XAUTHORITY}" "${target}"
echo "Prepared temporary X11 authorization for DISPLAY=${DISPLAY}."
