# Gazebo Demonstration Guide

This guide runs the live presentation views added after the Gate 7 evidence
freeze. They reuse the accepted ROS 2 packages, YOLOv8n v3 detector, estimator,
controller, and evaluator. They do not modify or replace the frozen Gate 1--7
results.

## What to show

| Mode | Purpose | Recorded result |
|---|---|---|
| `pair_turn` | One leader and one follower during a gradual turn | Passed: 0.104 m spacing RMSE, 97.3% `TRACK`, 50 ms control-period p95, zero collision samples |
| `chain_straight` | One leader and three independently driven followers in predecessor-following order | Passed: 0.058, 0.051, and 0.050 m spacing RMSE; 95%, 99%, and 97% `TRACK`; zero collision samples |
| `recovery` | One validated pair during a 1.3-second synthetic RGB blackout | Passed: `PREDICT` and `SAFE STOP` observed; zero command in `SAFE STOP`; 0.40 s reacquisition; zero collision samples |

The chain view shows Follower 1's RGB image and the supervisor state of all
three followers. This reduces presentation-only observer load. Each follower's
normal detector still receives its own camera stream.

## Start a live demonstration

Run these commands from the project root on the logged-in Hyprland desktop:

```bash
make gazebo-demo DEMO_MODE=pair_turn
make gazebo-demo DEMO_MODE=chain_straight
make gazebo-demo DEMO_MODE=recovery
```

Each command builds the four required ROS packages, opens Gazebo Sim and the
read-only dashboard, runs one bounded experiment, writes a timestamped result
below `work/ros2_ws/results/demo_runs/`, and closes the windows when the
evaluator completes.

The equivalent VS Code task is **EE616: Launch Gazebo demonstration**. It
prompts for the mode. Use **EE616: Open demo inspection shell** to
inspect ROS topics during a separate live run.

## Record a video

```bash
make gazebo-demo-record DEMO_MODE=pair_turn
make gazebo-demo-record DEMO_MODE=chain_straight
make gazebo-demo-record DEMO_MODE=recovery
```

The recorder moves the Gazebo and dashboard windows to Hyprland workspace 9,
records the focused monitor at 1920 by 1080 and 30 frames per second, then
returns to the previous workspace. It uses VA-API hardware encoding on
`/dev/dri/renderD128` when available and falls back to CPU encoding otherwise.
Set `EE616_RECORD_MONITOR` to a Hyprland monitor name if the automatic focused
monitor is not the desired one.

The three output files are:

- `deliverables/Neeraj_Kanchani_EE616_Gazebo_Pair_Turn_Demo.mp4`
- `deliverables/Neeraj_Kanchani_EE616_Gazebo_Three_Follower_Chain_Demo.mp4`
- `deliverables/Neeraj_Kanchani_EE616_Gazebo_Recovery_Demo.mp4`

Verify the final files from `deliverables/` with:

```bash
sha256sum -c Neeraj_Kanchani_EE616_Gazebo_Demo_SHA256SUMS.txt
```

## What the windows mean

Gazebo shows the simulated world, leader, followers, and their physical motion.
The dashboard subscribes to existing ROS topics and publishes nothing into the
robot stack. Its header shows the current supervisor state and experiment event.

- `TRACK`: a recent valid camera measurement updates the estimate.
- `PREDICT`: the measurement is temporarily missing, so the estimator predicts
  for a bounded interval.
- `SAFE_STOP`: the estimate is stale, so the follower commands zero linear and
  angular velocity.
- A black dashboard image during `LONG_OCCLUSION` is an intentional synthetic
  full-frame blackout, not a rendering failure.

Gazebo pose truth is read only by `ee616_evaluation` to calculate metrics. It is
not published to detection, estimation, supervision, control, or the disturbance
proxy.

## Interpretation

For the pair video: "This is the minimum scientific unit. The leader owns the
route. The follower uses its forward RGB camera and local odometry. Gazebo pose
data is used only by the evaluator."

For the chain video: "Each follower runs the same isolated pipeline and tracks
only its immediate predecessor. This video demonstrates the three-follower
topology in a straight aisle. The frozen experiment matrix contains repeated
straight and turn trials."

For the recovery video: "I intentionally remove the RGB image for 1.3 seconds.
The controller first predicts for a bounded time, then commands a safe stop when
the estimate becomes stale, and returns to tracking after the target reappears."

Use the words "simulated," "recorded," and "under this defined evaluator."
Do not say that these videos prove physical-robot performance, person safety,
certification, general string stability, or production readiness.

## Gazebo interaction

Use the left mouse button to select an entity. Use the normal Gazebo view tools
to orbit, pan, zoom, move to an entity, or follow it. Avoid spawning or moving
robots during a measured run because that changes the experiment. If you want
to explore freely, use the warehouse playground instead:

```bash
make gazebo-gui
```

## Troubleshooting

- If `DISPLAY` is unset, start the command from the logged-in desktop terminal.
- If the XWayland check fails, confirm that Hyprland's XWayland support is
  enabled and that `xdpyinfo -display "$DISPLAY"` works as the current user.
- If the Gazebo pane is blank, confirm that the display-enabled container reports
  `OpenGL vendor string: NVIDIA Corporation`. The compose overlay selects native
  NVIDIA PRIME rendering for this laptop.
- Do not set `LIBGL_ALWAYS_SOFTWARE=1`; Ogre2/EGL software rendering was tested
  and crashed on this configuration.
- The optional OGRE1 GUI engine was tested and did not create usable windows on
  this stack. The supported presentation path is native NVIDIA OpenGL with
  Gazebo's default OGRE2 engine.
- Stop a live project simulation with `bash infrastructure/dev/stop_simulation.sh`.
- A failed or interrupted presentation run remains separate from frozen gate
  evidence. Read its timestamped JSON summary before quoting any metric.

## Evidence boundary

The recorded videos are presentation artifacts. The repeated headless matrices
under `work/ros2_ws/results/pair_gate/`, `chain_gate/`, `disturbance_gate/`, and
`timing_gate/` remain the primary scientific evidence. A successful live video
does not replace repeated trials, and a GUI-loaded run is not used to rewrite
the frozen results.
