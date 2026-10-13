#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mode="${1:-pair_turn}"
case "${mode}" in
    pair_turn)
        filename=Neeraj_Kanchani_EE616_Gazebo_Pair_Turn_Demo.mp4
        ;;
    chain_straight|chain_turn)
        filename=Neeraj_Kanchani_EE616_Gazebo_Three_Follower_Chain_Demo.mp4
        ;;
    recovery)
        filename=Neeraj_Kanchani_EE616_Gazebo_Recovery_Demo.mp4
        ;;
    *)
        echo "Usage: $0 {pair_turn|chain_straight|chain_turn|recovery}" >&2
        exit 2
        ;;
esac

for command in hyprctl jq wf-recorder; do
    if ! command -v "${command}" >/dev/null 2>&1; then
        echo "Required host command is missing: ${command}" >&2
        exit 1
    fi
done

monitor="${EE616_RECORD_MONITOR:-$(hyprctl monitors -j | jq -r \
    'map(select(.focused))[0].name // .[0].name')}"
previous_workspace="$(hyprctl activeworkspace -j | jq -r '.id')"
demo_workspace="${EE616_DEMO_WORKSPACE:-9}"
output="${project_root}/deliverables/${filename}"
log_dir="${project_root}/work/ros2_ws/log/gazebo_demo_recording"
mkdir -p "${log_dir}"
log_path="${log_dir}/${mode}.log"

demo_pid=""
recorder_pid=""
cleanup() {
    if [[ -n "${recorder_pid}" ]] && kill -0 "${recorder_pid}" 2>/dev/null; then
        kill -INT "${recorder_pid}" 2>/dev/null || true
        wait "${recorder_pid}" 2>/dev/null || true
    fi
    if [[ -n "${demo_pid}" ]] && kill -0 "${demo_pid}" 2>/dev/null; then
        kill -INT -- "-${demo_pid}" 2>/dev/null || true
        wait "${demo_pid}" 2>/dev/null || true
    fi
    hyprctl dispatch workspace "${previous_workspace}" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

hyprctl dispatch workspace "${demo_workspace}" >/dev/null

setsid make -C "${project_root}" gazebo-demo \
    DEMO_MODE="${mode}" >"${log_path}" 2>&1 &
demo_pid=$!

ready=0
gazebo_address=""
dashboard_address=""
for _attempt in $(seq 1 90); do
    if ! kill -0 "${demo_pid}" 2>/dev/null; then
        echo "Demo exited before its dashboard appeared. See ${log_path}" >&2
        exit 1
    fi
    clients="$(hyprctl clients -j)"
    gazebo_address="$(jq -r \
        '.[] | select(.title == "Gazebo Sim") | .address' \
        <<<"${clients}" | head -n 1)"
    dashboard_address="$(jq -r \
        '.[] | select(.title | contains("EE616 follower cameras")) | .address' \
        <<<"${clients}" | head -n 1)"
    if [[ -n "${gazebo_address}" && -n "${dashboard_address}" ]]; then
        ready=1
        break
    fi
    sleep 1
done
if [[ "${ready}" -ne 1 ]]; then
    echo "Timed out waiting for the camera dashboard. See ${log_path}" >&2
    exit 1
fi

hyprctl dispatch movetoworkspacesilent \
    "${demo_workspace},address:${gazebo_address}" >/dev/null
hyprctl dispatch movetoworkspacesilent \
    "${demo_workspace},address:${dashboard_address}" >/dev/null
hyprctl dispatch workspace "${demo_workspace}" >/dev/null
sleep 2

echo "Recording ${mode} on monitor ${monitor} to ${output}"
recorder_args=(-y -D -r 30 -o "${monitor}" -f "${output}")
record_device="${EE616_RECORD_DEVICE:-/dev/dri/renderD128}"
if [[ -r "${record_device}" && -w "${record_device}" ]]; then
    echo "Using VA-API hardware encoding on ${record_device}."
    recorder_args=(-y -D -c h264_vaapi -d "${record_device}" -r 30 -o "${monitor}" -f "${output}")
else
    echo "VA-API device ${record_device} is unavailable; using CPU encoding."
fi
wf-recorder "${recorder_args[@]}" &
recorder_pid=$!
wait "${demo_pid}"
demo_pid=""
kill -INT "${recorder_pid}" 2>/dev/null || true
wait "${recorder_pid}"
recorder_pid=""
hyprctl dispatch workspace "${previous_workspace}" >/dev/null
trap - EXIT INT TERM
echo "Recorded ${output}"
